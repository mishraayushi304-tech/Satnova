from fastapi import APIRouter, HTTPException, status, Header, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from firebase.firestore_service import get_all_projects, get_chat_history
from utils.logger import logger

router = APIRouter(tags=["Projects & History"])


class ProjectSummary(BaseModel):
    project_id: str
    image_id: str
    filename: str
    user_id: str
    created_at: str
    updated_at: str
    status: str
    query_count: int
    report_ids: List[str] = []


class ProjectsResponse(BaseModel):
    total: int
    projects: List[dict]


@router.get("/projects", response_model=ProjectsResponse)
async def list_projects(
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Returns all satellite analysis projects for a user.
    Each project contains the image_id, filename, query count, and report links.
    If Firebase is not configured, returns empty list gracefully.
    """
    logger.info(f"[ProjectsAPI] Fetching projects for user_id='{user_id or 'anonymous'}'")
    projects = get_all_projects(user_id=user_id)

    return ProjectsResponse(
        total=len(projects),
        projects=projects
    )
