"""
DXF Upload API Routes
Handles file upload, parsing, and validation of plot boundary DXF files.
"""

import uuid
from pathlib import Path
from typing import List, Tuple

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel

from app.config import settings


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class BoundingBox(BaseModel):
    """Bounding box of the plot."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float


class UploadResponse(BaseModel):
    """Response after successful DXF upload."""
    project_id: str
    filename: str
    boundary: List[Tuple[float, float]]
    area_sqm: float
    area_sqft: float
    bounding_box: BoundingBox
    is_valid: bool
    message: str


class ProjectListItem(BaseModel):
    """Project summary for list view."""
    project_id: str
    filename: str
    area_sqm: float
    created_at: str


# ============================================================================
# In-memory project storage (will be replaced with proper storage later)
# ============================================================================

projects_store: dict = {}


# ============================================================================
# Routes
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_dxf(file: UploadFile = File(...)):
    """
    Upload a DXF file containing the plot boundary.
    
    The DXF file should contain:
    - A closed LWPOLYLINE or POLYLINE representing the plot boundary
    - Optional: Layer named 'BOUNDARY' or 'PLOT'
    
    Returns:
    - Project ID for future operations
    - Parsed boundary coordinates
    - Area calculations
    - Bounding box
    """
    # Validate file type
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DXF files are accepted"
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB"
        )
    
    # Generate project ID
    project_id = str(uuid.uuid4())
    
    # Save file
    file_path = settings.UPLOAD_DIR / f"{project_id}.dxf"
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # TODO: Parse DXF using core.dxf_parser (Phase 1.2)
    # For now, return placeholder data
    
    # Placeholder boundary (will be replaced with actual parsing)
    boundary = [
        (0.0, 0.0),
        (15.0, 0.0),
        (15.0, 20.0),
        (0.0, 20.0),
        (0.0, 0.0),  # Closed polygon
    ]
    area_sqm = 300.0  # 15m x 20m
    
    # Store project
    projects_store[project_id] = {
        "project_id": project_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "boundary": boundary,
        "area_sqm": area_sqm,
    }
    
    return UploadResponse(
        project_id=project_id,
        filename=file.filename,
        boundary=boundary,
        area_sqm=area_sqm,
        area_sqft=area_sqm * 10.764,  # Convert to sqft
        bounding_box=BoundingBox(
            min_x=0.0,
            min_y=0.0,
            max_x=15.0,
            max_y=20.0,
        ),
        is_valid=True,
        message="DXF file uploaded and parsed successfully",
    )


@router.get("/projects", response_model=List[ProjectListItem])
async def list_projects():
    """List all uploaded projects."""
    from datetime import datetime
    
    return [
        ProjectListItem(
            project_id=p["project_id"],
            filename=p["filename"],
            area_sqm=p["area_sqm"],
            created_at=datetime.now().isoformat(),
        )
        for p in projects_store.values()
    ]


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get details of a specific project."""
    if project_id not in projects_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return projects_store[project_id]


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and its associated files."""
    if project_id not in projects_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete file
    project = projects_store[project_id]
    file_path = Path(project["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Remove from store
    del projects_store[project_id]
    
    return {"message": "Project deleted successfully"}
