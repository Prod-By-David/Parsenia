from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str


class Project(BaseModel):
    id: str
    name: str
    created_at: str


projects: list[Project] = []


@router.get("")
async def get_projects():
    return {
        "success": True,
        "projects": projects,
    }


@router.post("")
async def create_project(data: ProjectCreate):
    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="El nombre del proyecto no puede estar vacío.",
        )

    project = Project(
        id=str(uuid4()),
        name=name,
        created_at=datetime.now().isoformat(),
    )

    projects.append(project)

    return {
        "success": True,
        "project": project,
    }


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    for index, project in enumerate(projects):
        if project.id == project_id:
            deleted_project = projects.pop(index)

            return {
                "success": True,
                "project": deleted_project,
            }

    raise HTTPException(
        status_code=404,
        detail="Proyecto no encontrado.",
    )