import os
from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from schemas.query_schema import QueryRequest, QueryResponse, ExecutionSummary
from services.langgraph_router import route_query
from firebase.firestore_service import save_chat_message, get_chat_history
from utils.logger import logger

router = APIRouter(tags=["AI Query Processing"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Core AI Query Endpoint — routes to LangGraph AI orchestration engine.
    Saves every Q&A exchange to Firestore chat_history for project memory.
    """
    logger.info(f"[QueryAPI] image_id='{request.image_id}' | Query: '{request.query}'")

    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty. Please ask a question about the satellite image."
        )

    result = route_query(
        image_id=request.image_id,
        query=request.query,
        pair_id=request.pair_id,
        upload_dir=UPLOAD_DIR
    )

    if result.get("error") == "IMAGE_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Satellite image with ID '{request.image_id}' not found. Please upload the image first."
        )

    exec_summary = result.get("execution_summary", {})

    # Save Q&A to Firestore chat_history
    save_chat_message(
        project_id=request.pair_id or request.image_id,
        image_id=request.image_id,
        query=request.query,
        answer=result["answer"],
        task=result["task"],
        model_used=result["model_used"],
        confidence=result["confidence"],
        processing_time=exec_summary.get("processing_time", "N/A"),
        user_id=user_id
    )

    return QueryResponse(
        image_id=request.image_id,
        query=request.query,
        task=result["task"],
        answer=result["answer"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        execution_summary=ExecutionSummary(
            image_type=exec_summary.get("image_type", "Satellite Image"),
            tools=exec_summary.get("tools", result["model_used"]),
            processing_time=exec_summary.get("processing_time", "N/A")
        ),
        overlay_image_path=result.get("overlay_image_path"),
        metadata=result.get("metadata")
    )


@router.get("/chat-history/{project_id}")
async def get_project_chat_history(project_id: str):
    """
    Returns the full chat/query history for a given project_id.
    Every question asked in a session is stored and retrievable.
    """
    history = get_chat_history(project_id)
    return {
        "project_id": project_id,
        "total_messages": len(history),
        "messages": history
    }
