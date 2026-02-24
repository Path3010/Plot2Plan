"""
Scoring system for candidate floor-plan layouts.

Evaluates layouts on three axes:
  1. **Area accuracy** — how close each room's area is to its target.
  2. **Adjacency satisfaction** — how many desired adjacencies are met.
  3. **Corridor penalty** — unused space inside the boundary.
"""

from typing import Dict, List, Optional

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .adjacency import build_adjacency_graph, is_connected
from .room_model import Room


# ---------------------------------------------------------------------------
# Individual scoring components
# ---------------------------------------------------------------------------

def area_accuracy_score(rooms: List[Room]) -> float:
    """
    Score ∈ [0, 1].  1.0 means every room hit its target area exactly.

    Uses: ``1 - mean(|actual - target| / target)`` clamped to [0, 1].
    """
    if not rooms:
        return 0.0
    errors = []
    for r in rooms:
        if r.target_area <= 0:
            continue
        err = abs(r.area - r.target_area) / r.target_area
        errors.append(min(err, 1.0))  # cap individual error at 100 %
    if not errors:
        return 1.0
    return max(0.0, 1.0 - (sum(errors) / len(errors)))


def adjacency_score(rooms: List[Room],
                     desired_adjacencies: Optional[List[tuple]] = None) -> float:
    """
    Score ∈ [0, 1].  1.0 means all desired adjacencies exist.

    Parameters
    ----------
    rooms : list[Room]
        Layout rooms.
    desired_adjacencies : list[tuple], optional
        Each tuple is ``(room_type_a, room_type_b)``.  If omitted, the
        score is based solely on graph connectivity.
    """
    room_dicts = [
        {"room_id": r.room_id, "room_type": r.room_type, "polygon": r.polygon}
        for r in rooms
    ]
    graph = build_adjacency_graph(room_dicts)

    if not is_connected(graph):
        return 0.0  # disconnected layout is invalid

    if not desired_adjacencies:
        return 1.0  # no specific requirements — connected is good enough

    # Build a type → id map
    type_to_ids: Dict[str, list] = {}
    for r in rooms:
        type_to_ids.setdefault(r.room_type, []).append(r.room_id)

    satisfied = 0
    for type_a, type_b in desired_adjacencies:
        ids_a = type_to_ids.get(type_a, [])
        ids_b = type_to_ids.get(type_b, [])
        found = False
        for ia in ids_a:
            for ib in ids_b:
                if graph.has_edge(ia, ib):
                    found = True
                    break
            if found:
                break
        if found:
            satisfied += 1

    return satisfied / len(desired_adjacencies)


def corridor_penalty(rooms: List[Room], boundary: Polygon) -> float:
    """
    Penalty ∈ [0, 1].  0.0 = no wasted space, 1.0 = all wasted.

    Wasted space = boundary area minus the union of room areas.
    """
    if boundary.area <= 0:
        return 0.0
    polys = [r.polygon for r in rooms]
    merged = unary_union(polys)
    covered = merged.intersection(boundary).area
    wasted_fraction = 1.0 - (covered / boundary.area)
    return max(0.0, min(1.0, wasted_fraction))


def shape_quality_score(rooms: List[Room]) -> float:
    """
    Score ∈ [0, 1].  1.0 means all rooms have good proportions.

    Penalises extreme aspect ratios — rooms should be roughly
    1:1 to 1:2 for residential use.
    """
    if not rooms:
        return 1.0
    penalties = []
    for r in rooms:
        if r.room_type == "entrance":
            continue  # skip entrance
        minx, miny, maxx, maxy = r.polygon.bounds
        w = maxx - minx
        h = maxy - miny
        if w < 0.01 or h < 0.01:
            penalties.append(1.0)
            continue
        ar = max(w / h, h / w)
        if ar <= 1.5:
            penalties.append(0.0)
        elif ar <= 2.2:
            penalties.append((ar - 1.5) / 0.7 * 0.5)
        else:
            penalties.append(1.0)
    if not penalties:
        return 1.0
    return max(0.0, 1.0 - (sum(penalties) / len(penalties)))


# ---------------------------------------------------------------------------
# Combined score
# ---------------------------------------------------------------------------

def score_layout(
    rooms: List[Room],
    boundary: Polygon,
    desired_adjacencies: Optional[List[tuple]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Compute the total score for a candidate layout.

    Parameters
    ----------
    rooms : list[Room]
        The candidate rooms.
    boundary : Polygon
        The usable building polygon.
    desired_adjacencies : list[tuple], optional
        Pairs of (room_type_a, room_type_b) that should be adjacent.
    weights : dict, optional
        Override default component weights.  Keys: ``area``, ``adjacency``,
        ``corridor``, ``shape``.

    Returns
    -------
    dict
        ``total``, ``area``, ``adjacency``, ``corridor``, ``shape`` scores.
    """
    w = weights or {
        "area": 0.30, "adjacency": 0.25, "corridor": 0.20, "shape": 0.25,
    }

    s_area = area_accuracy_score(rooms)
    s_adj = adjacency_score(rooms, desired_adjacencies)
    s_corr = 1.0 - corridor_penalty(rooms, boundary)  # higher is better
    s_shape = shape_quality_score(rooms)

    total = (
        w.get("area", 0.30) * s_area
        + w.get("adjacency", 0.25) * s_adj
        + w.get("corridor", 0.20) * s_corr
        + w.get("shape", 0.25) * s_shape
    )

    return {
        "total": round(total, 4),
        "area": round(s_area, 4),
        "adjacency": round(s_adj, 4),
        "corridor": round(s_corr, 4),
        "shape": round(s_shape, 4),
    }
