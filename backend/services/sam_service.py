"""
GroundingDINO + SAM2 Service (Object Grounding & Segmentation)
--------------------------------------------------------------
Responsibilities:
  - GroundingDINO: Detects and draws bounding boxes around named objects
    in satellite images (e.g. "Where is the river?", "Find roads").
  - SAM2: Generates precise pixel-level segmentation masks for the
    detected bounding box regions.

Pipeline Flow:
  User Query ("Highlight rivers")
       ↓
  GroundingDINO → Bounding Box coordinates
       ↓
  SAM2 → Pixel-perfect segmentation mask
       ↓
  Combined overlay image saved to uploads/

NOTE (SIH Hackathon Mode):
  Runs in MOCK mode during development. Replace mock block with
  actual model inference on GPU-equipped servers.
"""

import os
import time
from utils.logger import logger

MOCK_MODE = os.getenv("MOCK_AI", "true").lower() == "true"


def run_grounding_dino(image_path: str, text_prompt: str) -> dict:
    """
    Runs GroundingDINO open-vocabulary object detection on satellite image.

    Args:
        image_path:   Path to satellite image.
        text_prompt:  Object to detect (e.g. "river", "road", "building").

    Returns:
        dict with detected bounding boxes and confidence scores.
    """
    logger.info(f"[GroundingDINO] Detecting '{text_prompt}' in: {image_path}")
    start = time.time()

    if MOCK_MODE:
        time.sleep(0.5)
        result = {
            "detected_objects": [
                {
                    "label": text_prompt,
                    "confidence": 0.94,
                    "bbox": [142, 89, 623, 401]  # [x_min, y_min, x_max, y_max]
                },
                {
                    "label": text_prompt,
                    "confidence": 0.87,
                    "bbox": [712, 204, 980, 560]
                }
            ],
            "object_count": 2
        }
    else:
        # ── REAL MODEL INFERENCE ─────────────────────────────────────────────
        # from groundingdino.util.inference import load_model, load_image, predict
        # model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py",
        #                    "weights/groundingdino_swint_ogc.pth")
        # image_source, image = load_image(image_path)
        # boxes, logits, phrases = predict(
        #     model=model, image=image,
        #     caption=text_prompt, box_threshold=0.35, text_threshold=0.25
        # )
        # result = {"detected_objects": [{"label": p, "confidence": float(l), "bbox": b.tolist()}
        #           for p, l, b in zip(phrases, logits, boxes)], "object_count": len(boxes)}
        raise NotImplementedError("GroundingDINO real inference requires GPU. Set MOCK_AI=true.")

    elapsed = round(time.time() - start, 2)
    logger.info(f"[GroundingDINO] Detected {result['object_count']} object(s) in {elapsed}s")
    return {**result, "processing_time": f"{elapsed} seconds"}


def run_sam2_segmentation(image_path: str, bboxes: list) -> dict:
    """
    Runs SAM2 (Segment Anything Model 2) to generate pixel-level masks
    for the bounding boxes detected by GroundingDINO.

    Args:
        image_path: Path to satellite image.
        bboxes:     List of bounding boxes from GroundingDINO.

    Returns:
        dict with mask paths and segmentation area.
    """
    logger.info(f"[SAM2] Segmenting {len(bboxes)} region(s) in: {image_path}")
    start = time.time()

    if MOCK_MODE:
        time.sleep(0.8)
        result = {
            "masks_generated": len(bboxes),
            "segmented_area_percent": 18.4,
            "overlay_image_path": image_path.replace("uploads/", "uploads/seg_")
        }
    else:
        # ── REAL MODEL INFERENCE ─────────────────────────────────────────────
        # from sam2.build_sam import build_sam2
        # from sam2.sam2_image_predictor import SAM2ImagePredictor
        # import numpy as np
        # from PIL import Image
        # sam2 = build_sam2("sam2_hiera_large.yaml", "weights/sam2_hiera_large.pt")
        # predictor = SAM2ImagePredictor(sam2)
        # image = np.array(Image.open(image_path).convert("RGB"))
        # predictor.set_image(image)
        # masks, scores, _ = predictor.predict(box=np.array(bboxes), multimask_output=False)
        # result = {"masks_generated": len(masks), "segmented_area_percent": float(masks.sum() / masks.size * 100)}
        raise NotImplementedError("SAM2 real inference requires GPU. Set MOCK_AI=true.")

    elapsed = round(time.time() - start, 2)
    logger.info(f"[SAM2] Segmentation completed in {elapsed}s | Area: {result['segmented_area_percent']}%")
    return {**result, "processing_time": f"{elapsed} seconds"}


def run_grounding_and_segmentation(image_path: str, query: str) -> dict:
    """
    Full pipeline: GroundingDINO detection → SAM2 segmentation.
    Used for queries like "Highlight rivers", "Show me roads", "Locate buildings".
    """
    logger.info(f"[Grounding+SAM2] Full pipeline started for query: '{query}'")

    # Step 1: Extract target object from query
    text_prompt = _extract_target_object(query)

    # Step 2: GroundingDINO detection
    dino_result = run_grounding_dino(image_path, text_prompt)
    bboxes = [obj["bbox"] for obj in dino_result.get("detected_objects", [])]

    if not bboxes:
        return {
            "answer": f"No '{text_prompt}' detected in the satellite image.",
            "confidence": 0.0,
            "model_used": ["GroundingDINO"],
            "processing_time": dino_result["processing_time"]
        }

    # Step 3: SAM2 segmentation on detected boxes
    sam_result = run_sam2_segmentation(image_path, bboxes)

    answer = (
        f"Detection complete. Found {dino_result['object_count']} '{text_prompt}' region(s) in the satellite image. "
        f"Segmented area covers approximately {sam_result['segmented_area_percent']}% of the image. "
        f"Segmentation masks generated and overlay image saved."
    )

    total_time = round(
        float(dino_result["processing_time"].split()[0]) +
        float(sam_result["processing_time"].split()[0]), 2
    )

    return {
        "answer": answer,
        "confidence": dino_result["detected_objects"][0]["confidence"] * 100,
        "model_used": ["GroundingDINO", "SAM2"],
        "overlay_image_path": sam_result.get("overlay_image_path"),
        "processing_time": f"{total_time} seconds",
        "detection_details": dino_result
    }


def _extract_target_object(query: str) -> str:
    """
    Extracts the target object name from a user's natural language query.
    E.g. "Highlight rivers" → "river", "Detect roads" → "road"
    """
    skip_words = {"highlight", "detect", "find", "locate", "show", "where", "is", "the",
                  "me", "are", "mark", "identify", "segment", "extract", "a", "an", "in",
                  "this", "image", "satellite"}
    words = query.lower().replace("?", "").replace(".", "").split()
    meaningful = [w for w in words if w not in skip_words]
    return " ".join(meaningful) if meaningful else "object"
