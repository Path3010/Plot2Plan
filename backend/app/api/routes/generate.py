"""
Floor Generation API Routes
Handles floor plan generation for each floor level.
"""

from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================================================
# Enums and Types
# ============================================================================

class LayoutStrategy(str, Enum):
    """Available layout strategies."""
    COMPACT = "compact"
    L_SHAPE = "l_shape"
    COURTYARD = "courtyard"


class ZoneType(str, Enum):
    """Zone types for room allocation."""
    PUBLIC = "public"
    PRIVATE = "private"
    SERVICE = "service"
    CIRCULATION = "circulation"


# ============================================================================
# Request/Response Models
# ============================================================================

class SetbackConfig(BaseModel):
    """Setback configuration for buildable area calculation."""
    front: float = Field(default=3.0, ge=0, description="Front setback in meters")
    back: float = Field(default=2.0, ge=0, description="Back setback in meters")
    left: float = Field(default=1.5, ge=0, description="Left setback in meters")
    right: float = Field(default=1.5, ge=0, description="Right setback in meters")


class ZoneDistribution(BaseModel):
    """Zone distribution percentages."""
    public: float = Field(default=0.40, ge=0, le=1)
    private: float = Field(default=0.40, ge=0, le=1)
    service: float = Field(default=0.20, ge=0, le=1)


class FloorGenerationRequest(BaseModel):
    """Request body for floor generation."""
    project_id: str
    strategy: LayoutStrategy = LayoutStrategy.COMPACT
    required_rooms: List[str] = []
    zone_distribution: Optional[ZoneDistribution] = None
    options: Dict[str, Any] = {}


class RoomData(BaseModel):
    """Generated room data."""
    id: str
    type: str
    zone: ZoneType
    polygon: List[tuple]
    area_sqm: float
    doors: List[dict] = []
    windows: List[dict] = []


class StaircaseData(BaseModel):
    """Staircase placement data."""
    type: str
    polygon: List[tuple]
    entry_direction: str
    floor_connects: List[int]


class ScoreBreakdown(BaseModel):
    """Layout score breakdown."""
    total: float
    area_efficiency: float
    ventilation: float
    circulation: float
    adjacency: float
    orientation: float
    proportion: float


class FloorGenerationResponse(BaseModel):
    """Response after floor generation."""
    floor_number: int
    floor_name: str
    buildable_area_sqm: float
    rooms: List[RoomData]
    staircase: Optional[StaircaseData]
    corridor_area_sqm: float
    score: ScoreBreakdown
    preview_svg: Optional[str] = None


# ============================================================================
# Routes
# ============================================================================

@router.post("/generate/setback")
async def calculate_setback(
    project_id: str,
    setback: SetbackConfig = SetbackConfig()
):
    """
    Calculate buildable area by applying setback rules to plot boundary.
    
    Returns the buildable area polygon and statistics.
    """
    # TODO: Implement using core.setback_engine (Phase 2)
    
    return {
        "project_id": project_id,
        "setback_config": setback.model_dump(),
        "buildable_area": [
            (3.0, 3.0),
            (13.5, 3.0),
            (13.5, 18.0),
            (3.0, 18.0),
            (3.0, 3.0),
        ],
        "buildable_area_sqm": 157.5,  # Placeholder
        "coverage_ratio": 0.525,
        "message": "Setback calculation placeholder - will be implemented in Phase 2"
    }


@router.post("/generate/floor/{floor_number}", response_model=FloorGenerationResponse)
async def generate_floor(
    floor_number: int,
    request: FloorGenerationRequest
):
    """
    Generate a floor plan for the specified floor number.
    
    - Floor 0: Ground Floor
    - Floor 1: First Floor
    - Floor 2+: Upper Floors
    
    The staircase position is determined on Ground Floor and
    remains constant across all floors.
    """
    if floor_number < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor number must be non-negative"
        )
    
    # TODO: Implement using core.room_generator (Phase 4)
    
    # Floor names
    floor_names = {
        0: "Ground Floor",
        1: "First Floor",
        2: "Second Floor",
        3: "Third Floor",
    }
    floor_name = floor_names.get(floor_number, f"Floor {floor_number}")
    
    # Placeholder response
    return FloorGenerationResponse(
        floor_number=floor_number,
        floor_name=floor_name,
        buildable_area_sqm=157.5,
        rooms=[
            RoomData(
                id="room_001",
                type="living_room",
                zone=ZoneType.PUBLIC,
                polygon=[(3.0, 3.0), (8.0, 3.0), (8.0, 8.0), (3.0, 8.0)],
                area_sqm=25.0,
                doors=[{"position": [5.5, 3.0], "width": 1.0}],
                windows=[{"position": [3.0, 5.5], "width": 1.5}],
            ),
        ],
        staircase=StaircaseData(
            type="l_shaped",
            polygon=[(11.0, 14.0), (13.5, 14.0), (13.5, 18.0), (11.0, 18.0)],
            entry_direction="south",
            floor_connects=[0, 1],
        ) if floor_number < 2 else None,
        corridor_area_sqm=12.5,
        score=ScoreBreakdown(
            total=0.82,
            area_efficiency=0.88,
            ventilation=0.75,
            circulation=0.90,
            adjacency=0.78,
            orientation=0.85,
            proportion=0.80,
        ),
        preview_svg=None,
    )


@router.get("/generate/floor/{floor_number}/preview")
async def get_floor_preview(project_id: str, floor_number: int):
    """
    Get SVG preview of a generated floor plan.
    """
    # TODO: Implement SVG generation
    return {
        "floor_number": floor_number,
        "preview_svg": "<svg><!-- Placeholder --></svg>",
        "message": "SVG preview placeholder"
    }


@router.post("/generate/floor/{floor_number}/regenerate")
async def regenerate_floor(
    floor_number: int,
    request: FloorGenerationRequest
):
    """
    Regenerate a floor with different parameters or random seed.
    """
    # Reuse generate_floor logic
    return await generate_floor(floor_number, request)
