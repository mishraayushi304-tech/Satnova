"""
Firebase Storage Service
------------------------
Handles uploading satellite images from local staging (uploads/)
to Firebase Cloud Storage for permanent persistence.

Storage Folder Structure:
  satellite_images/{image_id}/{filename}   → Raw uploaded satellite images
  reports/{report_id}/{filename}           → Generated PDF reports

Returns a public download URL that can be stored in Firestore
and sent to the frontend for file access.
"""

import os
from typing import Optional
from utils.logger import logger
from firebase.config import get_storage_bucket


def upload_image_to_storage(image_id: str, local_path: str) -> Optional[str]:
    """
    Uploads a staged satellite image to Firebase Cloud Storage.

    Args:
        image_id:   Unique image identifier (used as storage folder name).
        local_path: Full local path to the staged file.

    Returns:
        Public download URL string, or None if upload fails or Firebase not configured.
    """
    bucket = get_storage_bucket()
    if not bucket:
        logger.warning("[Firebase Storage] Storage not configured. Skipping cloud upload.")
        return None

    try:
        filename = os.path.basename(local_path)
        storage_path = f"satellite_images/{image_id}/{filename}"

        blob = bucket.blob(storage_path)
        blob.upload_from_filename(local_path)
        blob.make_public()

        download_url = blob.public_url
        logger.info(f"[Firebase Storage] Image uploaded: {storage_path} → {download_url}")
        return download_url

    except Exception as e:
        logger.error(f"[Firebase Storage] Failed to upload image '{local_path}': {str(e)}")
        return None


def upload_report_to_storage(report_id: str, local_pdf_path: str) -> Optional[str]:
    """
    Uploads a generated PDF report to Firebase Cloud Storage.

    Args:
        report_id:      Unique report identifier.
        local_pdf_path: Full local path to the generated PDF file.

    Returns:
        Public download URL for the report, or None on failure.
    """
    bucket = get_storage_bucket()
    if not bucket:
        logger.warning("[Firebase Storage] Storage not configured. Skipping report upload.")
        return None

    try:
        filename = os.path.basename(local_pdf_path)
        storage_path = f"reports/{report_id}/{filename}"

        blob = bucket.blob(storage_path)
        blob.upload_from_filename(local_pdf_path, content_type="application/pdf")
        blob.make_public()

        download_url = blob.public_url
        logger.info(f"[Firebase Storage] Report uploaded: {storage_path} → {download_url}")
        return download_url

    except Exception as e:
        logger.error(f"[Firebase Storage] Failed to upload report '{local_pdf_path}': {str(e)}")
        return None
