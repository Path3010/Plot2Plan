"""
Zone Allocator Module
Divides buildable area into Public, Private, and Service zones.
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from shapely.geometry import Polygon, box
from shapely.ops import split
from shapely.affinity import translate


class ZoneType(str, Enum):
    """Types of zones in floor plan."""
    PUBLIC = "public"
    PRIVATE = "private"
    SERVICE = "service"
    CIRCULATION = "circulation"


@dataclass
class Zone:
    """Represents a zone in the floor plan."""
    type: ZoneType
    polygon: Polygon
    area_sqm: float
    target_percentage: float
    actual_percentage: float
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "polygon": list(self.polygon.exterior.coords),
            "area_sqm": self.area_sqm,
            "target_percentage": self.target_percentage,
            "actual_percentage": self.actual_percentage,
        }


@dataclass
class ZoneDistribution:
    """Target zone distribution percentages."""
    public: float = 0.40
    private: float = 0.40
    service: float = 0.20
    
    def validate(self) -> bool:
        """Check if percentages sum to 1.0."""
        total = self.public + self.private + self.service
        return abs(total - 1.0) < 0.01


class ZoneAllocator:
    """
    Allocates zones within the buildable area.
    
    Supports different allocation strategies based on plot orientation
    and layout style (compact, L-shape, courtyard).
    """
    
    # Zone placement strategies
    STRATEGY_FRONT_PUBLIC = "front_public"  # Public at front (default)
    STRATEGY_SIDE_SERVICE = "side_service"  # Service on one side
    STRATEGY_COURTYARD = "courtyard"        # Zones around courtyard
    
    def __init__(
        self,
        buildable_area: Polygon,
        front_direction: str = "S",
    ):
        """
        Initialize zone allocator.
        
        Args:
            buildable_area: Buildable area polygon
            front_direction: Direction facing the street (N, S, E, W)
        """
        self.buildable_area = buildable_area
        self.front_direction = front_direction.upper()
        self.zones: List[Zone] = []
        
    def allocate(
        self,
        distribution: ZoneDistribution,
        strategy: str = STRATEGY_FRONT_PUBLIC,
    ) -> List[Zone]:
        """
        Allocate zones based on distribution and strategy.
        
        Args:
            distribution: Target zone distribution
            strategy: Zone placement strategy
            
        Returns:
            List of Zone objects
        """
        if not distribution.validate():
            raise ValueError("Zone distribution must sum to 1.0")
        
        if strategy == self.STRATEGY_COURTYARD:
            self.zones = self._allocate_courtyard(distribution)
        else:
            self.zones = self._allocate_linear(distribution, strategy)
        
        return self.zones
    
    def _allocate_linear(
        self,
        distribution: ZoneDistribution,
        strategy: str,
    ) -> List[Zone]:
        """
        Allocate zones in a linear fashion (front-to-back or side-by-side).
        """
        bounds = self.buildable_area.bounds
        minx, miny, maxx, maxy = bounds
        width = maxx - minx
        height = maxy - miny
        total_area = self.buildable_area.area
        
        zones = []
        
        # Determine split direction based on front direction and strategy
        if self.front_direction in ["N", "S"]:
            # Split horizontally (top to bottom)
            zones = self._split_horizontal(
                minx, miny, maxx, maxy,
                distribution, total_area
            )
        else:
            # Split vertically (left to right)
            zones = self._split_vertical(
                minx, miny, maxx, maxy,
                distribution, total_area
            )
        
        return zones
    
    def _split_horizontal(
        self,
        minx: float, miny: float, maxx: float, maxy: float,
        distribution: ZoneDistribution,
        total_area: float,
    ) -> List[Zone]:
        """Split buildable area horizontally into zones."""
        height = maxy - miny
        zones = []
        
        # Calculate heights for each zone based on distribution
        public_height = height * distribution.public
        private_height = height * distribution.private
        service_height = height * distribution.service
        
        # Front direction determines which zone is at front
        if self.front_direction == "S":
            # Public at bottom (front), Private in middle, Service at top (back)
            y_positions = [
                (miny, miny + public_height, ZoneType.PUBLIC, distribution.public),
                (miny + public_height, miny + public_height + private_height, ZoneType.PRIVATE, distribution.private),
                (miny + public_height + private_height, maxy, ZoneType.SERVICE, distribution.service),
            ]
        else:  # N
            # Public at top (front), Private in middle, Service at bottom (back)
            y_positions = [
                (maxy - public_height, maxy, ZoneType.PUBLIC, distribution.public),
                (maxy - public_height - private_height, maxy - public_height, ZoneType.PRIVATE, distribution.private),
                (miny, maxy - public_height - private_height, ZoneType.SERVICE, distribution.service),
            ]
        
        for y_start, y_end, zone_type, target_pct in y_positions:
            zone_poly = box(minx, y_start, maxx, y_end)
            # Intersect with buildable area to handle irregular shapes
            zone_poly = zone_poly.intersection(self.buildable_area)
            
            if zone_poly.is_empty or zone_poly.area < 1:
                continue
            
            zones.append(Zone(
                type=zone_type,
                polygon=zone_poly,
                area_sqm=zone_poly.area,
                target_percentage=target_pct,
                actual_percentage=zone_poly.area / total_area,
            ))
        
        return zones
    
    def _split_vertical(
        self,
        minx: float, miny: float, maxx: float, maxy: float,
        distribution: ZoneDistribution,
        total_area: float,
    ) -> List[Zone]:
        """Split buildable area vertically into zones."""
        width = maxx - minx
        zones = []
        
        public_width = width * distribution.public
        private_width = width * distribution.private
        service_width = width * distribution.service
        
        if self.front_direction == "E":
            # Public at right, Private in middle, Service at left
            x_positions = [
                (maxx - public_width, maxx, ZoneType.PUBLIC, distribution.public),
                (maxx - public_width - private_width, maxx - public_width, ZoneType.PRIVATE, distribution.private),
                (minx, maxx - public_width - private_width, ZoneType.SERVICE, distribution.service),
            ]
        else:  # W
            # Public at left, Private in middle, Service at right
            x_positions = [
                (minx, minx + public_width, ZoneType.PUBLIC, distribution.public),
                (minx + public_width, minx + public_width + private_width, ZoneType.PRIVATE, distribution.private),
                (minx + public_width + private_width, maxx, ZoneType.SERVICE, distribution.service),
            ]
        
        for x_start, x_end, zone_type, target_pct in x_positions:
            zone_poly = box(x_start, miny, x_end, maxy)
            zone_poly = zone_poly.intersection(self.buildable_area)
            
            if zone_poly.is_empty or zone_poly.area < 1:
                continue
            
            zones.append(Zone(
                type=zone_type,
                polygon=zone_poly,
                area_sqm=zone_poly.area,
                target_percentage=target_pct,
                actual_percentage=zone_poly.area / total_area,
            ))
        
        return zones
    
    def _allocate_courtyard(
        self,
        distribution: ZoneDistribution,
    ) -> List[Zone]:
        """
        Allocate zones around a central courtyard.
        
        Creates a courtyard in the center and distributes zones around it.
        """
        bounds = self.buildable_area.bounds
        minx, miny, maxx, maxy = bounds
        width = maxx - minx
        height = maxy - miny
        total_area = self.buildable_area.area
        
        # Create courtyard (25% of area in center)
        courtyard_factor = 0.25
        c_width = width * (courtyard_factor ** 0.5)
        c_height = height * (courtyard_factor ** 0.5)
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        
        courtyard = box(
            cx - c_width/2, cy - c_height/2,
            cx + c_width/2, cy + c_height/2
        )
        
        # Subtract courtyard from buildable area
        remaining = self.buildable_area.difference(courtyard)
        
        # Simplified: Use linear allocation on remaining area
        # TODO: Implement proper courtyard zone distribution
        
        zones = []
        
        # For now, return single combined zone (placeholder)
        zones.append(Zone(
            type=ZoneType.PUBLIC,
            polygon=remaining,
            area_sqm=remaining.area,
            target_percentage=1.0,
            actual_percentage=1.0,
        ))
        
        # Add courtyard as a special "circulation" zone
        zones.append(Zone(
            type=ZoneType.CIRCULATION,
            polygon=courtyard,
            area_sqm=courtyard.area,
            target_percentage=0.25,
            actual_percentage=courtyard.area / total_area,
        ))
        
        return zones
    
    def get_zone_by_type(self, zone_type: ZoneType) -> Optional[Zone]:
        """Get zone by type."""
        for zone in self.zones:
            if zone.type == zone_type:
                return zone
        return None
    
    def get_allocation_stats(self) -> dict:
        """Get statistics about zone allocation."""
        total_area = sum(z.area_sqm for z in self.zones)
        
        return {
            "total_area_sqm": total_area,
            "zones": [z.to_dict() for z in self.zones],
            "distribution_accuracy": self._calculate_accuracy(),
        }
    
    def _calculate_accuracy(self) -> float:
        """Calculate how close actual distribution is to target."""
        if not self.zones:
            return 0.0
        
        errors = [
            abs(z.actual_percentage - z.target_percentage)
            for z in self.zones
        ]
        
        return 1.0 - sum(errors) / len(errors)
