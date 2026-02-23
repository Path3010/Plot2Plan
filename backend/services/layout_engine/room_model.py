"""
Room model using Shapely polygons.

Each room is represented as a Shapely Polygon with metadata
including type, target area, and floor assignment.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from shapely.geometry import Polygon


@dataclass
class Room:
    """A single room in a floor plan layout."""

    room_type: str
    polygon: Polygon
    target_area: float
    floor: int = 0
    room_id: Optional[int] = None

    # Class-level ID counter
    _next_id: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        if self.room_id is None:
            self.room_id = Room._next_id
            Room._next_id += 1

    @property
    def area(self) -> float:
        """Computed area from the Shapely polygon."""
        return self.polygon.area

    @property
    def bounds(self):
        """Bounding box of the room polygon (minx, miny, maxx, maxy)."""
        return self.polygon.bounds

    @property
    def centroid(self):
        """Centroid point of the room polygon."""
        return self.polygon.centroid

    @property
    def area_ratio(self) -> float:
        """Ratio of actual area to target area. 1.0 = perfect."""
        if self.target_area <= 0:
            return 0.0
        return self.area / self.target_area

    def to_dict(self) -> dict:
        """Serialize room to a dictionary."""
        coords = list(self.polygon.exterior.coords)
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "polygon": coords,
            "area": round(self.area, 2),
            "target_area": round(self.target_area, 2),
            "floor": self.floor,
        }

    @staticmethod
    def from_rect(x: float, y: float, width: float, height: float,
                  room_type: str = "room", target_area: float = 0.0,
                  floor: int = 0) -> "Room":
        """
        Create a Room from rectangle parameters (x, y, width, height).

        Converts the old-style rectangle format into a Shapely Polygon:
            Polygon([(x, y), (x+w, y), (x+w, y+h), (x, y+h)])
        """
        polygon = Polygon([
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height),
        ])
        if target_area <= 0:
            target_area = polygon.area
        return Room(
            room_type=room_type,
            polygon=polygon,
            target_area=target_area,
            floor=floor,
        )

    @staticmethod
    def reset_counter():
        """Reset the auto-increment ID counter."""
        Room._next_id = 0

    def __repr__(self) -> str:
        return (
            f"Room(id={self.room_id}, type='{self.room_type}', "
            f"area={self.area:.2f}, target={self.target_area:.2f})"
        )
