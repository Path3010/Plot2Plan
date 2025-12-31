"""
Staircase Handler Module
Placeholder for Phase 5 implementation.
"""

from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from shapely.geometry import Polygon, box


class StaircaseType(str, Enum):
    """Types of staircases."""
    STRAIGHT = "straight"
    L_SHAPED = "l_shaped"
    U_SHAPED = "u_shaped"
    SPIRAL = "spiral"


@dataclass
class StaircaseConfig:
    """Configuration for staircase."""
    type: StaircaseType = StaircaseType.L_SHAPED
    width: float = 1.0  # meters
    floor_height: float = 3.0  # meters
    tread_depth: float = 0.25  # meters
    riser_height: float = 0.175  # meters


@dataclass
class Staircase:
    """Represents a staircase in the floor plan."""
    type: StaircaseType
    polygon: Polygon
    entry_direction: str  # N, S, E, W
    floor_number: int
    connects_to: int  # Floor it connects to
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "polygon": list(self.polygon.exterior.coords),
            "entry_direction": self.entry_direction,
            "floor_number": self.floor_number,
            "connects_to": self.connects_to,
            "area_sqm": self.polygon.area,
        }


class StaircaseHandler:
    """
    Handles staircase placement and consistency across floors.
    
    The staircase position determined on ground floor MUST remain
    constant across all upper floors.
    
    TODO: Full implementation in Phase 5
    """
    
    # Minimum dimensions by type
    DIMENSIONS = {
        StaircaseType.STRAIGHT: {"width": 1.0, "length": 4.0},
        StaircaseType.L_SHAPED: {"width": 3.0, "height": 3.0},
        StaircaseType.U_SHAPED: {"width": 2.5, "height": 4.5},
        StaircaseType.SPIRAL: {"diameter": 2.0},
    }
    
    def __init__(self):
        """Initialize staircase handler."""
        self.ground_floor_staircase: Optional[Staircase] = None
        self.staircases: dict = {}  # floor_number -> Staircase
    
    def place_staircase(
        self,
        buildable_area: Polygon,
        floor_number: int,
        config: StaircaseConfig = StaircaseConfig(),
        preferred_position: Optional[Tuple[float, float]] = None,
    ) -> Staircase:
        """
        Place staircase in the floor plan.
        
        For ground floor, determines optimal position.
        For upper floors, uses the ground floor position.
        
        Args:
            buildable_area: Available area for placement
            floor_number: Current floor number
            config: Staircase configuration
            preferred_position: Optional preferred center point
            
        Returns:
            Staircase object
        """
        if floor_number == 0:
            # Ground floor - determine position
            staircase = self._place_ground_floor(
                buildable_area, config, preferred_position
            )
            self.ground_floor_staircase = staircase
        else:
            # Upper floor - use ground floor position
            if self.ground_floor_staircase is None:
                raise ValueError("Ground floor staircase must be placed first")
            
            staircase = self._place_upper_floor(
                floor_number, config
            )
        
        self.staircases[floor_number] = staircase
        return staircase
    
    def _place_ground_floor(
        self,
        buildable_area: Polygon,
        config: StaircaseConfig,
        preferred_position: Optional[Tuple[float, float]],
    ) -> Staircase:
        """Place staircase on ground floor."""
        bounds = buildable_area.bounds
        minx, miny, maxx, maxy = bounds
        
        # Get dimensions based on type
        dims = self.DIMENSIONS[config.type]
        
        if config.type == StaircaseType.SPIRAL:
            # Circular staircase
            diameter = dims["diameter"]
            cx = preferred_position[0] if preferred_position else (minx + maxx) / 2
            cy = preferred_position[1] if preferred_position else (miny + maxy) / 2
            polygon = box(cx - diameter/2, cy - diameter/2, cx + diameter/2, cy + diameter/2)
            entry_direction = "S"
        else:
            # Rectangular staircase
            width = dims.get("width", config.width)
            height = dims.get("height", dims.get("length", 4.0))
            
            # Default position: near center-back of the building
            if preferred_position:
                cx, cy = preferred_position
            else:
                cx = (minx + maxx) / 2
                cy = maxy - height / 2 - 1.0  # 1m from back wall
            
            polygon = box(
                cx - width/2, cy - height/2,
                cx + width/2, cy + height/2
            )
            entry_direction = "S"  # Enter from south
        
        return Staircase(
            type=config.type,
            polygon=polygon,
            entry_direction=entry_direction,
            floor_number=0,
            connects_to=1,
        )
    
    def _place_upper_floor(
        self,
        floor_number: int,
        config: StaircaseConfig,
    ) -> Staircase:
        """Place staircase on upper floor using ground floor position."""
        gf = self.ground_floor_staircase
        
        # Use exact same polygon
        return Staircase(
            type=gf.type,
            polygon=gf.polygon,  # SAME polygon
            entry_direction=self._get_upper_entry(gf.entry_direction),
            floor_number=floor_number,
            connects_to=floor_number + 1,
        )
    
    def _get_upper_entry(self, ground_entry: str) -> str:
        """Determine entry direction for upper floor based on stair run."""
        # For L-shaped, entry alternates
        # For straight, entry is opposite
        opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
        return opposite.get(ground_entry, "N")
    
    def validate_consistency(self, floor_number: int) -> bool:
        """Validate that staircase is consistent with ground floor."""
        if floor_number == 0 or self.ground_floor_staircase is None:
            return True
        
        if floor_number not in self.staircases:
            return False
        
        gf = self.ground_floor_staircase
        current = self.staircases[floor_number]
        
        # Polygons must be identical
        return gf.polygon.equals(current.polygon)
    
    def get_staircase_footprint(self) -> Optional[Polygon]:
        """Get the staircase footprint polygon."""
        if self.ground_floor_staircase:
            return self.ground_floor_staircase.polygon
        return None
