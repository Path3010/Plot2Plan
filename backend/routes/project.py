"""Project API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Project, Room, ProjectStatus
from schemas import ProjectCreate, ProjectOut, RoomOut
import json

router = APIRouter(prefix="/api", tags=["project"])


@router.post("/project", response_model=dict)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new project."""
    project = Project(
        session_id=data.session_id,
        total_area=data.total_area,
    )
    db.add(project)
    await db.flush()
    return {"project_id": project.id, "status": "created"}


@router.get("/project/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms_result = await db.execute(select(Room).where(Room.project_id == project_id))
    rooms = rooms_result.scalars().all()

    return {
        "id": project.id,
        "session_id": project.session_id,
        "created_at": str(project.created_at),
        "total_area": project.total_area,
        "status": project.status.value if project.status else "drafting",
        "boundary_polygon": json.loads(project.boundary_polygon) if project.boundary_polygon else None,
        "generated_plan": json.loads(project.generated_plan) if project.generated_plan else None,
        "dxf_path": project.dxf_path,
        "model3d_path": project.model3d_path,
        "rooms": [
            {
                "id": r.id,
                "room_type": r.room_type.value if r.room_type else "other",
                "quantity": r.quantity,
                "desired_area": r.desired_area,
                "generated_polygon": json.loads(r.generated_polygon) if r.generated_polygon else None,
            }
            for r in rooms
        ],
    }
