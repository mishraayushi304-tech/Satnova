from fastapi import APIRouter
from pydantic import BaseModel
import time

router = APIRouter(prefix="/health", tags=["Health & Monitoring"])

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    service: str

START_TIME = time.time()

@router.get("", response_model=HealthResponse)
async def get_health_status():
    """
    Returns server status, version, and running uptime for ISRO SatQuery AI backend.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(time.time() - START_TIME, 2),
        service="SatNova Backend Server"
    )
