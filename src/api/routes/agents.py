"""Agent monitoring API endpoints."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.agent_monitor import AgentMonitorService

logger = logging.getLogger(__name__)

router = APIRouter()
service = AgentMonitorService()


class AgentUpdateRequest(BaseModel):
    """Request body for updating tasks file."""

    contents: str


@router.get("/agents")
async def list_agents():
    """List all agent projects with task files and status."""
    projects = service.list_projects()
    return {"projects": [project.to_dict() for project in projects]}


@router.get("/agents/{project_name}")
async def get_agent_tasks(project_name: str):
    """Get tasks file content for a specific project."""
    project = _find_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    contents = service.read_tasks_file(project.tasks_file)
    return {
        "name": project.name,
        "project_path": str(project.project_path),
        "tasks_file": str(project.tasks_file),
        "status": project.status,
        "status_updated_at": project.status_updated_at,
        "contents": contents,
    }


@router.put("/agents/{project_name}")
async def update_agent_tasks(project_name: str, payload: AgentUpdateRequest):
    """Update tasks file content for a specific project."""
    project = _find_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    service.write_tasks_file(project.tasks_file, payload.contents)
    return {"status": "success"}


def _find_project(project_name: str):
    projects = service.list_projects()
    for project in projects:
        if project.name == project_name:
            return project
    return None
