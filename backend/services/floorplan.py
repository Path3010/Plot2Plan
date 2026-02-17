"""
Floor Plan Generation Engine.

Implements a BSP-based room placement algorithm with Shapely geometry.
Handles irregular boundaries, room sizing, wall generation, door/window placement.
"""

import math
import random
from typing import Optional
from shapely.geometry import Polygon, box, LineString, MultiPolygon
from shapely.affinity import scale as shapely_scale, translate
from shapely.ops import unary_union
import json


# Default room sizes (sq ft) and aspect ratios
ROOM_DEFAULTS = {
    "master_bedroom": {"area": 200, "aspect": 1.5, "label": "Master Bedroom"},
    "bedroom": {"area": 150, "aspect": 1.5, "label": "Bedroom"},
    "bathroom": {"area": 50, "aspect": 1.0, "label": "Bathroom"},
    "kitchen": {"area": 150, "aspect": 1.2, "label": "Kitchen"},
    "living": {"area": 250, "aspect": 1.3, "label": "Living Room"},
    "dining": {"area": 120, "aspect": 1.2, "label": "Dining Room"},
    "study": {"area": 100, "aspect": 1.2, "label": "Study"},
    "garage": {"area": 200, "aspect": 1.5, "label": "Garage"},
    "hallway": {"area": 60, "aspect": 3.0, "label": "Hallway"},
    "balcony": {"area": 40, "aspect": 2.0, "label": "Balcony"},
    "pooja": {"area": 30, "aspect": 1.0, "label": "Pooja Room"},
    "store": {"area": 40, "aspect": 1.0, "label": "Store Room"},
    "other": {"area": 80, "aspect": 1.2, "label": "Room"},
}

WALL_THICKNESS = 0.5  # feet


def _normalize_boundary(polygon_coords: list, target_area: Optional[float] = None) -> Polygon:
    """
    Normalise polygon: ensure closed, counter-clockwise.
    If target_area given and different from polygon area, scale accordingly.
    """
    if polygon_coords[0] != polygon_coords[-1]:
        polygon_coords.append(polygon_coords[0])

    poly = Polygon(polygon_coords)

    # Ensure counter-clockwise
    if not poly.exterior.is_ccw:
        poly = Polygon(list(reversed(list(poly.exterior.coords))))

    # Make valid
    if not poly.is_valid:
        poly = poly.buffer(0)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda g: g.area)

    # Scale to target area if needed
    if target_area and abs(poly.area - target_area) > 1.0:
        scale_factor = math.sqrt(target_area / poly.area)
        centroid = poly.centroid
        poly = shapely_scale(poly, xfact=scale_factor, yfact=scale_factor, origin=centroid)

    return poly


def _compute_room_targets(rooms: list, total_area: float) -> list:
    """
    Assign target areas to rooms. If user provided desired_area, use that.
    Otherwise use defaults. Scale proportionally to fit total_area.
    """
    result = []
    for room in rooms:
        rtype = room.get("room_type", "other")
        qty = room.get("quantity", 1)
        desired = room.get("desired_area")
        defaults = ROOM_DEFAULTS.get(rtype, ROOM_DEFAULTS["other"])

        for i in range(qty):
            label = defaults["label"]
            if qty > 1:
                label = f"{label} {i + 1}"
            result.append({
                "room_type": rtype,
                "label": label,
                "target_area": desired if desired else defaults["area"],
                "aspect": defaults["aspect"],
            })

    # Scale areas proportionally within the boundary (minus wall space)
    usable_area = total_area * 0.85  # ~15% for walls/corridors
    total_target = sum(r["target_area"] for r in result)

    if total_target > 0:
        scale_factor = usable_area / total_target
        for r in result:
            r["target_area"] = round(r["target_area"] * scale_factor, 1)

    # Sort largest first for BSP placement
    result.sort(key=lambda r: r["target_area"], reverse=True)
    return result


def _split_rect(rect_poly: Polygon, area_ratio: float, split_vertical: bool) -> tuple:
    """
    Split a rectangle (polygon) into two rectangles at the given area ratio.
    Returns (rect_a, rect_b).
    """
    minx, miny, maxx, maxy = rect_poly.bounds
    w = maxx - minx
    h = maxy - miny

    if split_vertical:
        split_x = minx + w * area_ratio
        a = box(minx, miny, split_x, maxy)
        b = box(split_x, miny, maxx, maxy)
    else:
        split_y = miny + h * area_ratio
        a = box(minx, miny, maxx, split_y)
        b = box(minx, split_y, maxx, maxy)

    return a, b


def _bsp_partition(bounding_rect: Polygon, room_targets: list, boundary: Polygon) -> list:
    """
    Binary space partitioning: recursively split bounding rectangle to allocate rooms.
    Clip each result to the boundary polygon.
    """
    if len(room_targets) == 0:
        return []

    if len(room_targets) == 1:
        clipped = bounding_rect.intersection(boundary)
        if clipped.is_empty:
            clipped = bounding_rect
        if isinstance(clipped, MultiPolygon):
            clipped = max(clipped.geoms, key=lambda g: g.area)
        return [{"room": room_targets[0], "polygon": clipped}]

    # Find split point
    total_area = sum(r["target_area"] for r in room_targets)
    mid_point = len(room_targets) // 2
    area_a = sum(r["target_area"] for r in room_targets[:mid_point])
    ratio = area_a / total_area if total_area > 0 else 0.5

    # Decide split direction based on bounds
    minx, miny, maxx, maxy = bounding_rect.bounds
    w = maxx - minx
    h = maxy - miny
    split_vertical = w >= h

    rect_a, rect_b = _split_rect(bounding_rect, ratio, split_vertical)

    result_a = _bsp_partition(rect_a, room_targets[:mid_point], boundary)
    result_b = _bsp_partition(rect_b, room_targets[mid_point:], boundary)

    return result_a + result_b


def _generate_walls(room_results: list, boundary: Polygon) -> list:
    """Generate wall geometries from room polygons."""
    walls = []

    for result in room_results:
        poly = result["polygon"]
        if poly.is_empty or not poly.is_valid:
            continue
        # Create wall outline by buffering the boundary of each room
        wall_line = poly.boundary
        wall_poly = wall_line.buffer(WALL_THICKNESS / 2)
        walls.append({
            "type": "wall",
            "geometry": _poly_to_coords(wall_poly),
        })

    # Add outer boundary wall
    outer_wall = boundary.boundary.buffer(WALL_THICKNESS / 2)
    walls.append({
        "type": "outer_wall",
        "geometry": _poly_to_coords(outer_wall),
    })

    return walls


def _generate_doors(room_results: list) -> list:
    """Generate door positions on shared edges between rooms."""
    doors = []
    for i in range(len(room_results)):
        for j in range(i + 1, len(room_results)):
            poly_a = room_results[i]["polygon"]
            poly_b = room_results[j]["polygon"]
            if poly_a.is_empty or poly_b.is_empty:
                continue

            shared_edge = poly_a.boundary.intersection(poly_b.boundary)

            if not shared_edge.is_empty and shared_edge.length > 2.0:
                # Place door at midpoint of shared edge
                if shared_edge.geom_type == "LineString":
                    mid = shared_edge.interpolate(0.5, normalized=True)
                    doors.append({
                        "type": "door",
                        "position": [round(mid.x, 2), round(mid.y, 2)],
                        "width": 3.0,
                        "between": [
                            room_results[i]["room"]["label"],
                            room_results[j]["room"]["label"],
                        ],
                    })
                elif shared_edge.geom_type == "MultiLineString":
                    longest = max(shared_edge.geoms, key=lambda g: g.length)
                    mid = longest.interpolate(0.5, normalized=True)
                    doors.append({
                        "type": "door",
                        "position": [round(mid.x, 2), round(mid.y, 2)],
                        "width": 3.0,
                        "between": [
                            room_results[i]["room"]["label"],
                            room_results[j]["room"]["label"],
                        ],
                    })
    return doors


def _generate_windows(room_results: list, boundary: Polygon) -> list:
    """Place windows on exterior walls based on room type."""
    windows = []
    window_room_types = {"living", "master_bedroom", "bedroom", "study", "dining"}

    for result in room_results:
        rtype = result["room"]["room_type"]
        if rtype not in window_room_types:
            continue

        poly = result["polygon"]
        if poly.is_empty:
            continue

        # Find edges that touch the boundary
        room_boundary = poly.boundary
        outer = boundary.boundary
        touching = room_boundary.intersection(outer)

        if not touching.is_empty and touching.length > 2.0:
            if touching.geom_type == "LineString":
                mid = touching.interpolate(0.5, normalized=True)
                windows.append({
                    "type": "window",
                    "position": [round(mid.x, 2), round(mid.y, 2)],
                    "width": 4.0 if rtype == "living" else 3.0,
                    "room": result["room"]["label"],
                })
            elif touching.geom_type == "MultiLineString":
                for line in touching.geoms:
                    if line.length > 2.0:
                        mid = line.interpolate(0.5, normalized=True)
                        windows.append({
                            "type": "window",
                            "position": [round(mid.x, 2), round(mid.y, 2)],
                            "width": 4.0 if rtype == "living" else 3.0,
                            "room": result["room"]["label"],
                        })
                        break  # one window per room is enough

    return windows


def _poly_to_coords(poly) -> list:
    """Convert Shapely polygon to coordinate list."""
    if poly.is_empty:
        return []
    if isinstance(poly, MultiPolygon):
        poly = max(poly.geoms, key=lambda g: g.area)
    if poly.geom_type == "Polygon":
        return [[round(x, 2), round(y, 2)] for x, y in poly.exterior.coords]
    return []


def generate_floor_plan(
    boundary_polygon: list,
    rooms: list,
    total_area: Optional[float] = None,
) -> dict:
    """
    Main entry point: generate a complete floor plan.

    Args:
        boundary_polygon: List of [x,y] coordinates forming the boundary.
        rooms: List of dicts with room_type, quantity, desired_area.
        total_area: Total area in sq ft (for scaling).

    Returns:
        Dict with 'rooms', 'walls', 'doors', 'windows', 'boundary' data.
    """
    # Normalize boundary
    boundary = _normalize_boundary(boundary_polygon, total_area)
    actual_area = boundary.area

    if total_area is None:
        total_area = actual_area

    # Compute room targets
    room_targets = _compute_room_targets(rooms, total_area)

    # Get bounding rectangle
    minx, miny, maxx, maxy = boundary.bounds
    bounding_rect = box(minx, miny, maxx, maxy)

    # BSP partition
    room_results = _bsp_partition(bounding_rect, room_targets, boundary)

    # Generate architectural elements
    walls = _generate_walls(room_results, boundary)
    doors = _generate_doors(room_results)
    windows = _generate_windows(room_results, boundary)

    # Build result
    plan_rooms = []
    for result in room_results:
        coords = _poly_to_coords(result["polygon"])
        poly = result["polygon"]
        plan_rooms.append({
            "label": result["room"]["label"],
            "room_type": result["room"]["room_type"],
            "target_area": result["room"]["target_area"],
            "actual_area": round(poly.area, 2) if not poly.is_empty else 0,
            "polygon": coords,
            "centroid": [round(poly.centroid.x, 2), round(poly.centroid.y, 2)] if not poly.is_empty else [0, 0],
        })

    return {
        "boundary": _poly_to_coords(boundary),
        "total_area": round(actual_area, 2),
        "rooms": plan_rooms,
        "walls": walls,
        "doors": doors,
        "windows": windows,
    }
