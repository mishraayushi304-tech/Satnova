"""
Open-CD Change Detection Service (Bi-Temporal Image Comparison)
---------------------------------------------------------------
Responsibilities:
  - Takes two satellite images (before & after event).
  - Runs Open-CD change detection model to identify changed regions.
  - Returns change mask, changed area percentage, and change type.

Use Cases:
  - "What changed between these two images?"
  - "Show deforestation between 2023 and 2026."
  - "How much land was lost to urbanization?"

NOTE (SIH Hackathon Mode):
  Runs in MOCK mode during development. Replace mock block with
  actual Open-CD model inference on GPU-equipped servers.
"""

import os
import time
from services.geotiff_service import locate_image_path
from utils.logger import logger

MOCK_MODE = os.getenv("MOCK_AI", "true").lower() == "true"


def run_change_detection(before_id: str, after_id: str, upload_dir: str = "uploads") -> dict:
    """
    Runs Open-CD bi-temporal change detection between two satellite images.

    Args:
        before_id:   image_id of the pre-event satellite image.
        after_id:    image_id of the post-event satellite image.
        upload_dir:  Local staging directory.

    Returns:
        dict with change analysis results including area changed and change type.
    """
    before_path = locate_image_path(before_id, upload_dir)
    after_path  = locate_image_path(after_id, upload_dir)

    logger.info(f"[Open-CD] Change detection: '{before_path}' vs '{after_path}'")
    start = time.time()

    if MOCK_MODE:
        time.sleep(1.0)  # Simulate heavier model inference
        result = {
            "changed_area_percent": 22.8,
            "change_type": "Urban Expansion / Vegetation Loss",
            "change_classes": {
                "Urban growth": "12.3%",
                "Vegetation loss": "7.4%",
                "Water body change": "3.1%"
            },
            "change_map_path": before_path.replace("uploads\\", "uploads\\change_")
        }
    else:
        # ── REAL MODEL INFERENCE ─────────────────────────────────────────────
        # import torch
        # import numpy as np
        # from PIL import Image
        # from opencd.models import build_detector  # Open-CD library
        #
        # img_before = np.array(Image.open(before_path).convert("RGB"))
        # img_after  = np.array(Image.open(after_path).convert("RGB"))
        #
        # model = build_detector(cfg="configs/opencd/fc_ef_256x256_40k_levircd.py")
        # model.load_state_dict(torch.load("weights/opencd_levircd.pth"))
        # model.eval()
        #
        # with torch.no_grad():
        #     change_mask = model(img_before, img_after)
        # changed_area = float(change_mask.sum() / change_mask.size * 100)
        # result = {"changed_area_percent": changed_area, "change_type": "Detected Change"}
        raise NotImplementedError("Open-CD real inference requires GPU. Set MOCK_AI=true.")

    elapsed = round(time.time() - start, 2)
    logger.info(f"[Open-CD] Change detection completed in {elapsed}s | Changed: {result['changed_area_percent']}%")

    answer = (
        f"Change detection complete. {result['changed_area_percent']}% of the observed region has changed "
        f"between the two satellite images. Primary change type: {result['change_type']}. "
        f"Detailed breakdown — " +
        " | ".join([f"{k}: {v}" for k, v in result.get("change_classes", {}).items()])
    )

    return {
        "answer": answer,
        "confidence": 89.6,
        "model_used": ["Open-CD"],
        "change_details": result,
        "processing_time": f"{elapsed} seconds"
    }
