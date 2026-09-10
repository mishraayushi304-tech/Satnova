"""
Task Classifier Service
-----------------------
Reads the user's natural language query and classifies it into one of the
predefined satellite analysis task types.

Task Types:
  - caption          → Describe the image (GeoChat / Qwen2-VL)
  - vqa              → Visual question answering (Qwen2-VL)
  - grounding        → Locate a specific object (GroundingDINO + SAM2)
  - segmentation     → Segment/highlight a region (SAM2)
  - change_detection → Compare before/after images (Open-CD)
  - vegetation       → Vegetation / NDVI analysis (Qwen2-VL + NDVI)
  - flood            → Flood detection & mapping (Qwen2-VL + SAM2)
  - optical_sar      → Optical + SAR dual analysis (Qwen2-VL + SAR logic)
"""

import re
from utils.logger import logger

# Keyword-to-task routing map
TASK_ROUTING_MAP = {
    "caption": [
        "describe", "what is in", "what do you see", "summarize", "overview",
        "explain the image", "tell me about", "what does this image show"
    ],
    "change_detection": [
        "change", "changed", "before after", "difference", "compare",
        "what changed", "evolution", "temporal", "land use change", "deforestation"
    ],
    "flood": [
        "flood", "flooded", "inundation", "waterlogged", "submerged",
        "water level", "flood extent", "flood area", "flood detection"
    ],
    "vegetation": [
        "vegetation", "ndvi", "plant", "forest", "crop", "green cover",
        "agriculture", "biomass", "deforestation", "tree cover", "greenery"
    ],
    "grounding": [
        "where is", "locate", "find", "detect", "highlight", "show me",
        "identify location", "mark the", "bounding box", "position of"
    ],
    "segmentation": [
        "segment", "mask", "outline", "draw", "boundary of", "region of",
        "extract area", "isolate", "separate", "delineate"
    ],
    "optical_sar": [
        "sar", "synthetic aperture", "radar", "backscatter",
        "optical sar", "dual polarization", "sentinel-1"
    ],
    "vqa": []   # Default fallback — general visual question
}

def classify_task(query: str) -> str:
    """
    Classifies the user's natural language query into a satellite analysis task type.

    Args:
        query: Raw user question string.

    Returns:
        Task type string (e.g. 'caption', 'grounding', 'flood', etc.)
    """
    query_lower = query.lower().strip()

    for task, keywords in TASK_ROUTING_MAP.items():
        if task == "vqa":
            continue  # Handled as default fallback
        for keyword in keywords:
            if keyword in query_lower:
                logger.info(f"Query classified as task='{task}' | Matched keyword='{keyword}' | Query='{query}'")
                return task

    logger.info(f"Query classified as task='vqa' (default VQA) | Query='{query}'")
    return "vqa"
