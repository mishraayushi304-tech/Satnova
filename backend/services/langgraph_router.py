"""
LangGraph AI Orchestration Router
----------------------------------
LangGraph is the "Backend Manager / Air Traffic Controller" of SatQuery AI.

It reads the classified task type and routes the request to the
correct AI model service(s), executes the pipeline, and
returns the merged execution result.

Routing Map:
  caption          → GeoChat (run_geochat_caption)
  vqa              → Qwen2-VL (run_qwen_vqa)
  grounding        → GroundingDINO + SAM2 (run_grounding_and_segmentation)
  segmentation     → SAM2 only (run_grounding_and_segmentation)
  change_detection → Open-CD (run_change_detection)
  vegetation       → Qwen2-VL NDVI (run_vegetation_analysis)
  flood            → Qwen2-VL + SAM2 (run_flood_analysis)
  optical_sar      → Qwen2-VL SAR mode (run_qwen_vqa)
  vqa (default)    → Qwen2-VL (run_qwen_vqa)

NOTE:
  This service uses the LangGraph state graph pattern with typed state dicts.
  In hackathon dev mode, it runs a simplified sequential router.
  Full LangGraph node wiring can be enabled after basic pipeline validation.
"""

import os
import time
from typing import TypedDict, Optional, Any

from services.task_classifier import classify_task
from services.qwen_service import (
    run_geochat_caption,
    run_qwen_vqa,
    run_flood_analysis,
    run_vegetation_analysis
)
from services.sam_service import run_grounding_and_segmentation
from services.change_service import run_change_detection
from services.geotiff_service import locate_image_path
from utils.logger import logger


# ─── LangGraph State Schema ──────────────────────────────────────────────────

class AgentState(TypedDict):
    """Typed state passed through every node in the LangGraph pipeline."""
    image_id: str
    image_path: str
    query: str
    task: str
    result: Optional[dict]
    error: Optional[str]
    pair_id: Optional[str]
    before_id: Optional[str]
    after_id: Optional[str]


# ─── Router Entry Point ───────────────────────────────────────────────────────

def route_query(
    image_id: str,
    query: str,
    pair_id: Optional[str] = None,
    before_id: Optional[str] = None,
    after_id: Optional[str] = None,
    upload_dir: str = "uploads"
) -> dict:
    """
    Main LangGraph router entry point.

    Accepts query + image_id, classifies the task, selects the AI tool(s),
    executes the pipeline, and returns a structured ISRO execution summary.

    Args:
        image_id:   ID of the primary uploaded satellite image.
        query:      User's natural language question.
        pair_id:    (Optional) ID of an image pair session (for change detection).
        before_id:  (Optional) Pre-event image ID for bi-temporal tasks.
        after_id:   (Optional) Post-event image ID for bi-temporal tasks.
        upload_dir: Directory where staged images are stored.

    Returns:
        Structured result dict with answer, confidence, model_used, execution_summary.
    """
    global_start = time.time()

    # STEP 1 — Classify Task
    task = classify_task(query)
    logger.info(f"[LangGraph] Task classified → '{task}' | Image: '{image_id}' | Query: '{query}'")

    # STEP 2 — Resolve image path
    try:
        image_path = locate_image_path(image_id, upload_dir)
    except FileNotFoundError:
        logger.error(f"[LangGraph] Image not found: {image_id}")
        return {
            "task": task,
            "answer": "Image not found. Please upload the satellite image first.",
            "confidence": 0.0,
            "model_used": [],
            "error": "IMAGE_NOT_FOUND"
        }

    # STEP 3 — Build LangGraph initial state
    state: AgentState = {
        "image_id": image_id,
        "image_path": image_path,
        "query": query,
        "task": task,
        "result": None,
        "error": None,
        "pair_id": pair_id,
        "before_id": before_id,
        "after_id": after_id
    }

    # STEP 4 — Execute task node
    state = _execute_task_node(state, upload_dir)

    total_time = round(time.time() - global_start, 2)

    result = state.get("result", {})
    if state.get("error"):
        return {
            "task": task,
            "answer": "An error occurred during AI analysis.",
            "confidence": 0.0,
            "model_used": [],
            "error": state["error"]
        }

    return {
        "task": task,
        "answer": result.get("answer", "Analysis complete."),
        "confidence": result.get("confidence", 85.0),
        "model_used": result.get("model_used", []),
        "overlay_image_path": result.get("overlay_image_path"),
        "metadata": result.get("detection_details") or result.get("change_details"),
        "execution_summary": {
            "image_type": _infer_image_type(image_path),
            "tools": result.get("model_used", []),
            "processing_time": f"{total_time} seconds"
        }
    }


# ─── Task Node Executor ───────────────────────────────────────────────────────

def _execute_task_node(state: AgentState, upload_dir: str) -> AgentState:
    """
    Executes the appropriate AI service based on task type.
    Maps each task type to its corresponding model service function.
    """
    task = state["task"]
    image_path = state["image_path"]
    query = state["query"]

    try:
        if task == "caption":
            result = run_geochat_caption(image_path)

        elif task == "vqa":
            result = run_qwen_vqa(image_path, query)

        elif task in ("grounding", "segmentation"):
            result = run_grounding_and_segmentation(image_path, query)

        elif task == "flood":
            result = run_flood_analysis(image_path)

        elif task == "vegetation":
            result = run_vegetation_analysis(image_path)

        elif task == "change_detection":
            before_id = state.get("before_id")
            after_id  = state.get("after_id")
            if not before_id or not after_id:
                state["error"] = "MISSING_PAIR_IDS"
                state["result"] = {
                    "answer": "Change detection requires both before_image_id and after_image_id.",
                    "confidence": 0.0,
                    "model_used": []
                }
                return state
            result = run_change_detection(before_id, after_id, upload_dir)

        elif task == "optical_sar":
            result = run_qwen_vqa(image_path, f"[SAR Analysis Mode] {query}")
            result["model_used"] = ["Qwen2-VL (SAR Mode)"]

        else:
            # Fallback default to VQA
            result = run_qwen_vqa(image_path, query)

        state["result"] = result

    except Exception as e:
        logger.error(f"[LangGraph] Task node execution failed for task='{task}': {str(e)}")
        state["error"] = str(e)
        state["result"] = {
            "answer": "AI model execution failed. Please try again.",
            "confidence": 0.0,
            "model_used": []
        }

    return state


# ─── Helper ──────────────────────────────────────────────────────────────────

def _infer_image_type(image_path: str) -> str:
    """Infers satellite sensor type from filename."""
    name_upper = os.path.basename(image_path).upper()
    if "SENTINEL-2" in name_upper or "S2" in name_upper:
        return "Sentinel-2 (Optical)"
    elif "SENTINEL-1" in name_upper or "S1" in name_upper:
        return "Sentinel-1 (SAR)"
    elif "LANDSAT" in name_upper or "LC08" in name_upper:
        return "Landsat-8/9 (Optical)"
    elif "CARTOSAT" in name_upper:
        return "Cartosat-3 (Optical)"
    elif "RISAT" in name_upper:
        return "RISAT-1A (SAR)"
    return "Satellite Optical Image"
