"""
Amenity Placer Module - Places external amenities in open plot spaces.
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
from shapely.geometry import Polygon, box


class AmenityType(str, Enum):
    SWIMMING_POOL = "swimming_pool"
    LAWN = "lawn"
    GARDEN = "garden"
    DRIVEWAY = "driveway"
    SERVANT_QUARTER = "servant_quarter"


@dataclass
class Amenity:
    type: AmenityType
    polygon: Polygon
    area_sqm: float = 0
    
    def __post_init__(self):
        if self.area_sqm == 0:
            self.area_sqm = self.polygon.area


class AmenityPlacer:
    """Places amenities in open plot spaces. TODO: Phase 8"""
    
    def __init__(self, plot_boundary: Polygon, building_footprint: Polygon):
        self.plot_boundary = plot_boundary
        self.building_footprint = building_footprint
        self.open_space = plot_boundary.difference(building_footprint)
        self.amenities: List[Amenity] = []
    
    def place_amenities(self, required: List[str]) -> List[Amenity]:
        self.amenities = []
        for atype in required:
            try:
                amenity = self._place_amenity(AmenityType(atype))
                if amenity:
                    self.amenities.append(amenity)
            except ValueError:
                pass
        return self.amenities
    
    def _place_amenity(self, atype: AmenityType) -> Optional[Amenity]:
        if self.open_space.area < 10:
            return None
        bounds = self.open_space.bounds
        poly = box(bounds[0], bounds[1], bounds[0] + 5, bounds[1] + 5)
        poly = poly.intersection(self.open_space)
        if poly.is_empty:
            return None
        self.open_space = self.open_space.difference(poly)
        return Amenity(type=atype, polygon=poly)
