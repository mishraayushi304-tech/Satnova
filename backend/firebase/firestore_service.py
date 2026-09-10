"""
Firebase Firestore Service
--------------------------
Handles all database read/write operations for SatQuery AI.

Firestore Collections:
  users/          → User profile and authentication records
  projects/       → Satellite analysis project sessions
  uploads/        → Per-image upload metadata records
  reports/        → Generated PDF report references
  chat_history/   → Full conversation history per project

NOTE:
  All Firestore operations fail gracefully when Firebase is not
  configured (local dev mode). A warning is logged and a mock
  response is returned so the API continues to function.
"""

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from utils.logger import logger
from firebase.config import get_db


def _get_firestore():
    """Returns Firestore client or None if not initialized."""
    db = get_db()
    if db is None:
        logger.warning("[Firestore] Firebase not configured. Skipping database operation.")
    return db


# ─────────────────────────────────────────────────────────────────────────────
# UPLOADS COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

def save_upload_record(
    image_id: str,
    filename: str,
    file_size_bytes: int,
    content_type: str,
    saved_path: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Saves an image upload record to Firestore uploads/ collection.
    Called automatically after every successful POST /upload.
    """
    db = _get_firestore()
    if not db:
        return False

    try:
        doc = {
            "image_id": image_id,
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "content_type": content_type,
            "saved_path": saved_path,
            "user_id": user_id or "anonymous",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "status": "staged"
        }
        db.collection("uploads").document(image_id).set(doc)
        logger.info(f"[Firestore] Upload record saved: uploads/{image_id}")
        return True
    except Exception as e:
        logger.error(f"[Firestore] Failed to save upload record: {str(e)}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PROJECTS COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

def create_project(
    image_id: str,
    filename: str,
    user_id: Optional[str] = None
) -> Optional[str]:
    """
    Creates a new satellite analysis project in Firestore projects/ collection.
    Returns the project_id on success.
    """
    db = _get_firestore()
    if not db:
        return None

    try:
        import uuid
        project_id = str(uuid.uuid4())
        doc = {
            "project_id": project_id,
            "image_id": image_id,
            "filename": filename,
            "user_id": user_id or "anonymous",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "query_count": 0,
            "report_ids": []
        }
        db.collection("projects").document(project_id).set(doc)
        logger.info(f"[Firestore] Project created: projects/{project_id}")
        return project_id
    except Exception as e:
        logger.error(f"[Firestore] Failed to create project: {str(e)}")
        return None


def get_all_projects(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves all projects from Firestore, optionally filtered by user_id.
    Used by GET /projects endpoint.
    """
    db = _get_firestore()
    if not db:
        return []

    try:
        collection = db.collection("projects")
        if user_id:
            query = collection.where("user_id", "==", user_id).order_by("created_at", direction="DESCENDING")
        else:
            query = collection.order_by("created_at", direction="DESCENDING")

        docs = query.stream()
        projects = [doc.to_dict() for doc in docs]
        logger.info(f"[Firestore] Retrieved {len(projects)} project(s)")
        return projects
    except Exception as e:
        logger.error(f"[Firestore] Failed to retrieve projects: {str(e)}")
        return []


def update_project_query_count(project_id: str) -> bool:
    """Increments the query_count field for a project."""
    db = _get_firestore()
    if not db:
        return False

    try:
        from google.cloud.firestore_v1 import Increment
        db.collection("projects").document(project_id).update({
            "query_count": Increment(1),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"[Firestore] Failed to update project query count: {str(e)}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CHAT HISTORY COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

def save_chat_message(
    project_id: str,
    image_id: str,
    query: str,
    answer: str,
    task: str,
    model_used: List[str],
    confidence: float,
    processing_time: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Saves a single query-answer exchange to Firestore chat_history/ collection.
    Called after every successful POST /query.
    """
    db = _get_firestore()
    if not db:
        return False

    try:
        import uuid
        chat_id = str(uuid.uuid4())
        doc = {
            "chat_id": chat_id,
            "project_id": project_id,
            "image_id": image_id,
            "user_id": user_id or "anonymous",
            "query": query,
            "answer": answer,
            "task": task,
            "model_used": model_used,
            "confidence": confidence,
            "processing_time": processing_time,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        db.collection("chat_history").document(chat_id).set(doc)
        logger.info(f"[Firestore] Chat message saved: chat_history/{chat_id}")
        return True
    except Exception as e:
        logger.error(f"[Firestore] Failed to save chat message: {str(e)}")
        return False


def get_chat_history(project_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all chat messages for a given project_id, ordered by timestamp.
    """
    db = _get_firestore()
    if not db:
        return []

    try:
        docs = (
            db.collection("chat_history")
            .where("project_id", "==", project_id)
            .order_by("timestamp")
            .stream()
        )
        history = [doc.to_dict() for doc in docs]
        logger.info(f"[Firestore] Retrieved {len(history)} chat message(s) for project '{project_id}'")
        return history
    except Exception as e:
        logger.error(f"[Firestore] Failed to retrieve chat history: {str(e)}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# REPORTS COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

def save_report_record(
    project_id: str,
    image_id: str,
    report_url: str,
    report_filename: str,
    user_id: Optional[str] = None
) -> Optional[str]:
    """
    Saves a generated PDF report reference to Firestore reports/ collection.
    """
    db = _get_firestore()
    if not db:
        return None

    try:
        import uuid
        report_id = str(uuid.uuid4())
        doc = {
            "report_id": report_id,
            "project_id": project_id,
            "image_id": image_id,
            "user_id": user_id or "anonymous",
            "report_url": report_url,
            "report_filename": report_filename,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        db.collection("reports").document(report_id).set(doc)

        # Link report to project
        db.collection("projects").document(project_id).update({
            "report_ids": __import__("google.cloud.firestore", fromlist=["ArrayUnion"]).ArrayUnion([report_id]),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        logger.info(f"[Firestore] Report record saved: reports/{report_id}")
        return report_id
    except Exception as e:
        logger.error(f"[Firestore] Failed to save report record: {str(e)}")
        return None
