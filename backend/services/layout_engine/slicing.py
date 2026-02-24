"""
Slicing Floorplan Generator with Architectural Zoning.

Uses a slicing-tree representation where each internal node is a
horizontal (H) or vertical (V) cut, and each leaf is a room.
The tree is optimised via simulated annealing so that:

  * Room areas match targets
  * Room aspect ratios stay reasonable (1:1 – 1:2)
  * Architectural zones are respected (public near entrance,
    private away, service rooms clustered)
  * Wet areas (kitchen, bathroom) share walls for plumbing alignment

Based on the classic VLSI slicing-floorplan formulation adapted for
residential architecture.
"""

import copy
import math
import random
from typing import Dict, List, Optional, Tuple

from shapely.geometry import Polygon, box


# ── Architectural zone definitions ────────────────────────────────────────

ZONE_MAP: Dict[str, str] = {
    "living":          "public",
    "dining":          "public",
    "porch":           "public",
    "entrance":        "public",
    "kitchen":         "service",
    "bathroom":        "service",
    "toilet":          "service",
    "utility":         "service",
    "master_bedroom":  "private",
    "bedroom":         "private",
    "study":           "private",
    "pooja":           "private",
    "store":           "service",
    "parking":         "public",
    "staircase":       "circulation",
}

# Desired adjacency bonus pairs (source, target) — rooms that benefit
# from sharing a wall.
ARCH_ADJACENCY = [
    ("living", "dining"),
    ("kitchen", "dining"),
    ("master_bedroom", "bathroom"),
    ("bedroom", "bathroom"),
    ("living", "entrance"),
    ("living", "porch"),
    ("kitchen", "utility"),
]

# Max acceptable aspect ratio (width/height or height/width)
MAX_ASPECT_RATIO = 2.2


# ── Slicing tree data structures ──────────────────────────────────────────

class _SliceNode:
    """Internal node of a slicing tree: either H-cut or V-cut."""

    __slots__ = ("cut", "ratio", "left", "right")

    def __init__(self, cut: str, ratio: float, left, right):
        self.cut = cut          # "H" or "V"
        self.ratio = ratio      # fraction [0.15 .. 0.85] for left child
        self.left = left
        self.right = right


class _LeafNode:
    """Leaf node — represents a single room."""

    __slots__ = ("room_type", "target_area", "zone", "room_idx")

    def __init__(self, room_type: str, target_area: float, room_idx: int):
        self.room_type = room_type
        self.target_area = target_area
        self.zone = ZONE_MAP.get(room_type, "private")
        self.room_idx = room_idx


# ── Tree construction ─────────────────────────────────────────────────────

def _build_initial_tree(
    room_specs: List[dict],
    boundary_width: float,
    boundary_height: float,
) -> _SliceNode:
    """
    Build an initial slicing tree that respects architectural zoning.

    Rooms are sorted by zone:
      public (near entrance) | service (clustered) | private (back)
    Then recursively split with alternating H/V cuts.
    """
    # Sort by zone priority: public first, then service, then private
    zone_order = {"public": 0, "circulation": 1, "service": 2, "private": 3}
    specs = sorted(room_specs, key=lambda s: zone_order.get(
        ZONE_MAP.get(s["room_type"], "private"), 3
    ))

    leaves = [
        _LeafNode(s["room_type"], s["target_area"], i)
        for i, s in enumerate(specs)
    ]

    return _build_subtree(leaves, True, boundary_width, boundary_height)


def _build_subtree(
    leaves: List[_LeafNode],
    vertical: bool,
    width: float,
    height: float,
) -> object:
    if len(leaves) == 1:
        return leaves[0]
    if len(leaves) == 0:
        return _LeafNode("void", 1.0, -1)

    # Split roughly in half by area
    total_area = sum(l.target_area for l in leaves)
    accum = 0.0
    split_idx = 1
    for i, leaf in enumerate(leaves):
        accum += leaf.target_area
        if accum >= total_area * 0.45:
            split_idx = max(1, i + 1)
            break

    left_leaves = leaves[:split_idx]
    right_leaves = leaves[split_idx:]

    if not right_leaves:
        right_leaves = [left_leaves.pop()]
    if not left_leaves:
        left_leaves = [right_leaves.pop(0)]

    left_area = sum(l.target_area for l in left_leaves)
    ratio = left_area / total_area if total_area > 0 else 0.5
    ratio = max(0.2, min(0.8, ratio))

    cut = "V" if vertical else "H"

    if cut == "V":
        left_w, left_h = width * ratio, height
        right_w, right_h = width * (1 - ratio), height
    else:
        left_w, left_h = width, height * ratio
        right_w, right_h = width, height * (1 - ratio)

    left = _build_subtree(left_leaves, not vertical, left_w, left_h)
    right = _build_subtree(right_leaves, not vertical, right_w, right_h)

    return _SliceNode(cut, ratio, left, right)


# ── Layout from tree ──────────────────────────────────────────────────────

def _evaluate_tree(
    node,
    x: float,
    y: float,
    w: float,
    h: float,
) -> List[dict]:
    """
    Walk the slicing tree and assign rectangles to leaves.

    Returns a list of ``{room_type, target_area, zone, room_idx, polygon}``.
    """
    if isinstance(node, _LeafNode):
        if w < 0.1 or h < 0.1:
            return []
        poly = box(x, y, x + w, y + h)
        return [{
            "room_type": node.room_type,
            "target_area": node.target_area,
            "zone": node.zone,
            "room_idx": node.room_idx,
            "polygon": poly,
        }]

    if node.cut == "V":
        lw = w * node.ratio
        rw = w - lw
        left_rooms = _evaluate_tree(node.left, x, y, lw, h)
        right_rooms = _evaluate_tree(node.right, x + lw, y, rw, h)
    else:
        lh = h * node.ratio
        rh = h - lh
        left_rooms = _evaluate_tree(node.left, x, y, w, lh)
        right_rooms = _evaluate_tree(node.right, x, y + lh, w, rh)

    return left_rooms + right_rooms


# ── Scoring ───────────────────────────────────────────────────────────────

def _aspect_ratio(poly: Polygon) -> float:
    """Aspect ratio ≥ 1.0; perfect square = 1.0."""
    minx, miny, maxx, maxy = poly.bounds
    w = maxx - minx
    h = maxy - miny
    if w < 0.01 or h < 0.01:
        return 99.0
    return max(w / h, h / w)


def _score_candidate(
    rooms: List[dict],
    boundary_area: float,
    desired_adjacencies: Optional[List[Tuple[str, str]]] = None,
) -> float:
    """
    Score a candidate layout.  Higher is better.  Range roughly [0, 1].

    Components:
      - area_accuracy   (weight 0.30) — room areas vs targets
      - shape_quality   (weight 0.25) — penalise extreme aspect ratios
      - adjacency_bonus (weight 0.25) — desired room pairs share a wall
      - coverage        (weight 0.20) — fills the boundary (no corridor waste)
    """
    if not rooms:
        return 0.0

    adj_pairs = desired_adjacencies or ARCH_ADJACENCY

    # ── Area accuracy ──
    area_errors = []
    for r in rooms:
        target = r["target_area"]
        actual = r["polygon"].area
        if target <= 0:
            continue
        err = abs(actual - target) / target
        area_errors.append(min(err, 1.0))
    area_acc = max(0.0, 1.0 - (sum(area_errors) / max(len(area_errors), 1)))

    # ── Shape quality ──
    aspect_penalties = []
    for r in rooms:
        ar = _aspect_ratio(r["polygon"])
        # 1.0 – 1.5: perfect; 1.5 – 2.0: slight penalty; >2.0: heavy penalty
        if ar <= 1.5:
            aspect_penalties.append(0.0)
        elif ar <= MAX_ASPECT_RATIO:
            aspect_penalties.append((ar - 1.5) / (MAX_ASPECT_RATIO - 1.5) * 0.5)
        else:
            aspect_penalties.append(1.0)
    shape_quality = max(0.0, 1.0 - (sum(aspect_penalties) / max(len(aspect_penalties), 1)))

    # ── Adjacency bonus ──
    # Two rooms are adjacent if their polygons share a boundary of length > 0.1
    type_to_polys: Dict[str, List[Polygon]] = {}
    for r in rooms:
        type_to_polys.setdefault(r["room_type"], []).append(r["polygon"])

    satisfied = 0
    possible = 0
    for ta, tb in adj_pairs:
        polys_a = type_to_polys.get(ta, [])
        polys_b = type_to_polys.get(tb, [])
        if not polys_a or not polys_b:
            continue
        possible += 1
        found = False
        for pa in polys_a:
            for pb in polys_b:
                shared = pa.intersection(pb)
                if shared.length > 0.1:
                    found = True
                    break
            if found:
                break
        if found:
            satisfied += 1
    adj_score = satisfied / max(possible, 1)

    # ── Coverage ──
    total_room_area = sum(r["polygon"].area for r in rooms)
    coverage = min(1.0, total_room_area / max(boundary_area, 1.0))

    # ── Weighted total ──
    total = (
        0.30 * area_acc
        + 0.25 * shape_quality
        + 0.25 * adj_score
        + 0.20 * coverage
    )
    return total


# ── Simulated annealing ──────────────────────────────────────────────────

def _collect_internal_nodes(node) -> List[_SliceNode]:
    """Collect all internal (non-leaf) nodes for mutation."""
    if isinstance(node, _LeafNode):
        return []
    result = [node]
    result.extend(_collect_internal_nodes(node.left))
    result.extend(_collect_internal_nodes(node.right))
    return result


def _collect_leaves(node) -> List[_LeafNode]:
    """Collect all leaf nodes."""
    if isinstance(node, _LeafNode):
        return [node]
    result = []
    result.extend(_collect_leaves(node.left))
    result.extend(_collect_leaves(node.right))
    return result


def _deep_copy_tree(node):
    """Deep-copy a slicing tree."""
    if isinstance(node, _LeafNode):
        new = _LeafNode(node.room_type, node.target_area, node.room_idx)
        return new
    new = _SliceNode(
        node.cut,
        node.ratio,
        _deep_copy_tree(node.left),
        _deep_copy_tree(node.right),
    )
    return new


def _mutate_tree(node) -> object:
    """
    Apply one random mutation to the tree:
      1. Adjust a split ratio (±0.05 – 0.15)
      2. Flip a cut direction (H↔V)
      3. Swap two leaves
    """
    tree = _deep_copy_tree(node)
    internals = _collect_internal_nodes(tree)
    leaves = _collect_leaves(tree)

    action = random.choices(
        ["ratio", "flip", "swap"],
        weights=[0.50, 0.25, 0.25],
        k=1,
    )[0]

    if action == "ratio" and internals:
        picked = random.choice(internals)
        delta = random.uniform(-0.15, 0.15)
        picked.ratio = max(0.15, min(0.85, picked.ratio + delta))

    elif action == "flip" and internals:
        picked = random.choice(internals)
        picked.cut = "V" if picked.cut == "H" else "H"

    elif action == "swap" and len(leaves) >= 2:
        a, b = random.sample(leaves, 2)
        # Swap room assignments
        a.room_type, b.room_type = b.room_type, a.room_type
        a.target_area, b.target_area = b.target_area, a.target_area
        a.zone, b.zone = b.zone, a.zone
        a.room_idx, b.room_idx = b.room_idx, a.room_idx

    return tree


def _simulated_annealing(
    tree,
    x: float,
    y: float,
    w: float,
    h: float,
    boundary_area: float,
    desired_adjacencies: Optional[List[Tuple[str, str]]] = None,
    iterations: int = 800,
    t_start: float = 1.0,
    t_end: float = 0.01,
) -> Tuple[object, List[dict], float]:
    """
    Optimise the slicing tree via simulated annealing.

    Returns (best_tree, best_rooms, best_score).
    """
    best_tree = _deep_copy_tree(tree)
    best_rooms = _evaluate_tree(best_tree, x, y, w, h)
    best_score = _score_candidate(best_rooms, boundary_area, desired_adjacencies)

    current_tree = _deep_copy_tree(tree)
    current_score = best_score

    for i in range(iterations):
        # Temperature schedule
        t = t_start * ((t_end / t_start) ** (i / max(iterations - 1, 1)))

        candidate_tree = _mutate_tree(current_tree)
        candidate_rooms = _evaluate_tree(candidate_tree, x, y, w, h)
        candidate_score = _score_candidate(candidate_rooms, boundary_area, desired_adjacencies)

        delta = candidate_score - current_score

        if delta > 0 or random.random() < math.exp(delta / max(t, 1e-10)):
            current_tree = candidate_tree
            current_score = candidate_score

            if current_score > best_score:
                best_tree = _deep_copy_tree(current_tree)
                best_rooms = candidate_rooms
                best_score = current_score

    return best_tree, best_rooms, best_score


# ── Public API ────────────────────────────────────────────────────────────

def generate_slicing_candidate(
    room_specs: List[dict],
    boundary_width: float,
    boundary_height: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    sa_iterations: int = 800,
    seed: Optional[int] = None,
    desired_adjacencies: Optional[List[Tuple[str, str]]] = None,
) -> Tuple[List[dict], float]:
    """
    Generate one optimised slicing-floorplan candidate.

    Parameters
    ----------
    room_specs : list[dict]
        ``[{"room_type": str, "target_area": float}, ...]``
    boundary_width, boundary_height : float
        Dimensions of the bounding rectangle.
    origin_x, origin_y : float
        Bottom-left corner offset.
    sa_iterations : int
        Number of simulated-annealing iterations per candidate.
    seed : int, optional
        Random seed for reproducibility.
    desired_adjacencies : list[tuple], optional
        ``[(type_a, type_b), ...]`` to reward in scoring.

    Returns
    -------
    (rooms, score)
        rooms: list of dicts with room_type, target_area, polygon, etc.
        score: float ∈ [0, 1].
    """
    if seed is not None:
        random.seed(seed)

    boundary_area = boundary_width * boundary_height

    tree = _build_initial_tree(room_specs, boundary_width, boundary_height)

    _, rooms, score = _simulated_annealing(
        tree,
        origin_x,
        origin_y,
        boundary_width,
        boundary_height,
        boundary_area,
        desired_adjacencies=desired_adjacencies,
        iterations=sa_iterations,
    )

    return rooms, score
