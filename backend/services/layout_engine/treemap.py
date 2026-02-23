"""
Treemap-based rectangular subdivision.

Implements squarified treemaps to partition a rectangle into
sub-rectangles with prescribed areas.  All outputs are Shapely Polygons.
"""

from typing import List, Tuple
from shapely.geometry import Polygon, box


class _Rect:
    """Axis-aligned rectangle used during treemap subdivision."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    @property
    def width(self) -> float:
        return abs(self.x2 - self.x1)

    @property
    def height(self) -> float:
        return abs(self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def is_horizontal(self) -> bool:
        return self.width >= self.height

    @property
    def aspect_ratio(self) -> float:
        """How far from square (0 = perfect square)."""
        if self.height == 0 or self.width == 0:
            return float("inf")
        return max(self.width / self.height, self.height / self.width) - 1

    # --- splitting --------------------------------------------------------

    def split_horizontal(self, area: float) -> Tuple["_Rect", "_Rect"]:
        """Split with a vertical line so that the left piece has *area*."""
        w = area / self.height if self.height else 0
        left = _Rect(self.x1, self.y1, self.x1 + w, self.y2)
        right = _Rect(self.x1 + w, self.y1, self.x2, self.y2)
        return left, right

    def split_vertical(self, area: float) -> Tuple["_Rect", "_Rect"]:
        """Split with a horizontal line so the bottom piece has *area*."""
        h = area / self.width if self.width else 0
        bottom = _Rect(self.x1, self.y1, self.x2, self.y1 + h)
        top = _Rect(self.x1, self.y1 + h, self.x2, self.y2)
        return bottom, top

    def split_auto(self, area: float) -> Tuple["_Rect", "_Rect"]:
        if self.is_horizontal:
            return self.split_horizontal(area)
        return self.split_vertical(area)

    # --- subdivision-------------------------------------------------------

    def _place_zone(self, areas: List[float]):
        """
        Place as many rooms as possible in one strip, minimizing total
        aspect-ratio error.  Returns (rooms, leftover_rect).
        """
        best_rooms = None
        best_leftover = None
        best_error = float("inf")

        for i in range(1, len(areas) + 1):
            zone_areas = areas[:i]
            zone_total = sum(zone_areas)
            zone_rect, leftover = self.split_auto(zone_total)

            rooms: List[_Rect] = []
            current = zone_rect
            for a in zone_areas:
                if self.is_horizontal:
                    room, current = current.split_vertical(a)
                else:
                    room, current = current.split_horizontal(a)
                rooms.append(room)

            error = _mean_aspect_error(rooms)
            if error > best_error:
                break  # previous was better
            best_error = error
            best_rooms = rooms
            best_leftover = leftover

        return best_rooms or [], best_leftover or self

    def subdivide(self, areas: List[float]) -> List["_Rect"]:
        """
        Recursively partition this rectangle into sub-rectangles whose
        areas match *areas* as closely as possible (squarified treemap).
        """
        if not areas:
            return []
        rooms, leftover = self._place_zone(areas)
        remaining = areas[len(rooms):]
        if remaining:
            rooms.extend(leftover.subdivide(remaining))
        return rooms

    def to_polygon(self) -> Polygon:
        """Convert to a Shapely Polygon."""
        return box(self.x1, self.y1, self.x2, self.y2)


def _mean_aspect_error(rects: List[_Rect]) -> float:
    if not rects:
        return 0.0
    return sum(r.aspect_ratio for r in rects) / len(rects)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def treemap_subdivide(
    width: float,
    height: float,
    areas: List[float],
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> List[Polygon]:
    """
    Partition a *width* x *height* rectangle into sub-rectangles.

    Parameters
    ----------
    width, height : float
        Overall dimensions (meters).
    areas : list[float]
        Desired area for each room.  Will be proportionally scaled to
        fill the total rectangle.
    origin_x, origin_y : float
        Bottom-left corner of the bounding rectangle.

    Returns
    -------
    list[Polygon]
        One Shapely Polygon per room.
    """
    total_rect_area = width * height
    total_wanted = sum(areas) if areas else 1.0
    scale = total_rect_area / total_wanted

    scaled = [a * scale for a in areas]

    bounding = _Rect(origin_x, origin_y, origin_x + width, origin_y + height)
    sub_rects = bounding.subdivide(scaled)

    return [r.to_polygon() for r in sub_rects]
