"""
Configuration API Routes
Provides access to system rules, room catalogs, and validation endpoints.
"""

from typing import Dict, List, Any

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class RoomSpec(BaseModel):
    """Room specification from catalog."""
    name: str
    zone: str
    min_area_sqft: float
    max_area_sqft: float
    aspect_ratio: tuple
    requires_ventilation: bool
    preferred_orientation: List[str]
    adjacent_to: List[str]


class SetbackRule(BaseModel):
    """Setback rule configuration."""
    front: float
    back: float
    sides: float
    max_coverage: float
    max_far: float


# ============================================================================
# Configuration Data
# ============================================================================

ROOM_CATALOG = {
    # Public Zone
    "living_room": {
        "name": "Living Room",
        "zone": "public",
        "min_area_sqft": 180,
        "max_area_sqft": 400,
        "aspect_ratio": (1.0, 2.0),
        "requires_ventilation": True,
        "preferred_orientation": ["N", "E"],
        "adjacent_to": ["foyer", "dining_room"],
    },
    "dining_room": {
        "name": "Dining Room",
        "zone": "public",
        "min_area_sqft": 120,
        "max_area_sqft": 200,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": ["E", "W"],
        "adjacent_to": ["living_room", "kitchen"],
    },
    "foyer": {
        "name": "Foyer",
        "zone": "circulation",
        "min_area_sqft": 40,
        "max_area_sqft": 80,
        "aspect_ratio": (1.0, 2.0),
        "requires_ventilation": False,
        "preferred_orientation": [],
        "adjacent_to": ["living_room", "staircase"],
    },
    # Private Zone
    "master_bedroom": {
        "name": "Master Bedroom",
        "zone": "private",
        "min_area_sqft": 150,
        "max_area_sqft": 250,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": ["N", "E"],
        "adjacent_to": ["master_bathroom", "walk_in_closet"],
    },
    "bedroom": {
        "name": "Bedroom",
        "zone": "private",
        "min_area_sqft": 100,
        "max_area_sqft": 180,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": ["N", "E", "W"],
        "adjacent_to": ["bathroom"],
    },
    "study": {
        "name": "Study",
        "zone": "private",
        "min_area_sqft": 80,
        "max_area_sqft": 120,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": ["N"],
        "adjacent_to": [],
    },
    # Service Zone
    "kitchen": {
        "name": "Kitchen",
        "zone": "service",
        "min_area_sqft": 80,
        "max_area_sqft": 150,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": ["E"],
        "adjacent_to": ["dining_room", "utility"],
    },
    "bathroom": {
        "name": "Bathroom",
        "zone": "service",
        "min_area_sqft": 35,
        "max_area_sqft": 60,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": [],
        "adjacent_to": [],
    },
    "master_bathroom": {
        "name": "Master Bathroom",
        "zone": "service",
        "min_area_sqft": 50,
        "max_area_sqft": 100,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": [],
        "adjacent_to": ["master_bedroom"],
    },
    "utility": {
        "name": "Utility Room",
        "zone": "service",
        "min_area_sqft": 40,
        "max_area_sqft": 80,
        "aspect_ratio": (1.0, 2.0),
        "requires_ventilation": True,
        "preferred_orientation": [],
        "adjacent_to": ["kitchen"],
    },
    "powder_room": {
        "name": "Powder Room",
        "zone": "service",
        "min_area_sqft": 20,
        "max_area_sqft": 35,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": [],
        "adjacent_to": [],
    },
    "servant_room": {
        "name": "Servant Room",
        "zone": "service",
        "min_area_sqft": 80,
        "max_area_sqft": 120,
        "aspect_ratio": (1.0, 1.5),
        "requires_ventilation": True,
        "preferred_orientation": [],
        "adjacent_to": ["servant_bathroom"],
    },
}

SETBACK_RULES = {
    "residential": {
        "front": 3.0,
        "back": 2.0,
        "sides": 1.5,
        "max_coverage": 0.60,
        "max_far": 2.0,
    },
    "commercial": {
        "front": 4.5,
        "back": 3.0,
        "sides": 2.0,
        "max_coverage": 0.65,
        "max_far": 2.5,
    },
}

ADJACENCY_MATRIX = {
    "living_room": {
        "required": ["foyer", "dining_room"],
        "preferred": ["staircase"],
        "forbidden": ["kitchen", "utility"],
    },
    "dining_room": {
        "required": ["kitchen"],
        "preferred": ["living_room"],
        "forbidden": ["bedroom", "bathroom"],
    },
    "kitchen": {
        "required": ["dining_room"],
        "preferred": ["utility"],
        "forbidden": ["bedroom", "master_bedroom"],
    },
    "master_bedroom": {
        "required": ["master_bathroom"],
        "preferred": ["walk_in_closet", "balcony"],
        "forbidden": ["kitchen", "living_room"],
    },
    "bedroom": {
        "required": [],
        "preferred": ["bathroom"],
        "forbidden": ["kitchen"],
    },
}


# ============================================================================
# Routes
# ============================================================================

@router.get("/rules/rooms", response_model=Dict[str, Any])
async def get_room_catalog():
    """
    Get the complete room catalog with specifications.
    """
    return {
        "rooms": ROOM_CATALOG,
        "zones": ["public", "private", "service", "circulation"],
    }


@router.get("/rules/rooms/{room_type}")
async def get_room_spec(room_type: str):
    """Get specification for a specific room type."""
    if room_type not in ROOM_CATALOG:
        return {"error": f"Room type '{room_type}' not found"}
    return ROOM_CATALOG[room_type]


@router.get("/rules/setbacks")
async def get_setback_rules():
    """Get setback rules by building type."""
    return SETBACK_RULES


@router.get("/rules/adjacency")
async def get_adjacency_matrix():
    """Get room adjacency requirements matrix."""
    return ADJACENCY_MATRIX


@router.get("/rules/strategies")
async def get_layout_strategies():
    """Get available layout strategies."""
    return {
        "strategies": [
            {
                "id": "compact",
                "name": "Compact",
                "description": "Efficient rectangular layout minimizing corridors",
                "best_for": "Small to medium plots",
            },
            {
                "id": "l_shape",
                "name": "L-Shape",
                "description": "L-shaped layout with outdoor space",
                "best_for": "Corner plots, medium plots",
            },
            {
                "id": "courtyard",
                "name": "Courtyard",
                "description": "Central courtyard with rooms around",
                "best_for": "Large plots, traditional style",
            },
        ]
    }


@router.get("/rules/amenities")
async def get_amenity_catalog():
    """Get available external amenity options."""
    return {
        "amenities": [
            {
                "id": "swimming_pool",
                "name": "Swimming Pool",
                "min_area_sqft": 300,
                "requires": ["pool_deck", "equipment_room"],
            },
            {
                "id": "lawn",
                "name": "Lawn",
                "min_area_sqft": 200,
                "flexible_shape": True,
            },
            {
                "id": "driveway",
                "name": "Driveway",
                "min_width_m": 3.0,
                "connects_to": "street",
            },
            {
                "id": "garden",
                "name": "Garden",
                "min_area_sqft": 100,
                "flexible_shape": True,
            },
            {
                "id": "servant_quarter",
                "name": "Servant Quarter",
                "area_sqft": 150,
                "separate_entry": True,
            },
        ]
    }


@router.post("/validate/polygon")
async def validate_polygon(coordinates: List[List[float]]):
    """
    Validate a polygon for use as plot boundary.
    
    Checks:
    - Polygon is closed
    - No self-intersections
    - Minimum area requirement
    - Valid coordinate format
    """
    # TODO: Implement using shapely (Phase 1.2)
    
    is_valid = True
    issues = []
    
    if len(coordinates) < 4:
        is_valid = False
        issues.append("Polygon must have at least 4 points (3 + closing point)")
    
    # Check if closed
    if coordinates and coordinates[0] != coordinates[-1]:
        is_valid = False
        issues.append("Polygon is not closed (first point != last point)")
    
    return {
        "is_valid": is_valid,
        "issues": issues,
        "point_count": len(coordinates),
    }
