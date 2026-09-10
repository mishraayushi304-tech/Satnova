import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Header
from typing import Optional
from schemas.upload_schema import ImageUploadResponse, ImagePairUploadResponse
from utils.logger import logger
from firebase.firestore_service import save_upload_record, create_project
from firebase.storage_service import upload_image_to_storage

router = APIRouter(tags=["Image Ingestion"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
ALLOWED_EXTENSIONS = tuple(os.getenv("ALLOWED_EXTENSIONS", ".tif,.tiff,.png,.jpg,.jpeg").lower().split(","))

os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_and_save_file(file: UploadFile) -> tuple:
    """
    Validates file extension and size, saves to local staging directory.
    Returns (image_id, saved_filepath, file_size_bytes).
    """
    safe_basename = os.path.basename(file.filename or "unknown")
    ext = os.path.splitext(safe_basename)[1].lower()
    if not ext or ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Upload rejected: invalid extension '{ext}' for file {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: GeoTIFF (.tif/.tiff), PNG (.png), JPEG (.jpg/.jpeg)"
        )

    image_id = str(uuid.uuid4())
    filename = f"{image_id}_{safe_basename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    try:
        contents = file.file.read()
        file_size = len(contents)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes). Please provide a valid satellite image."
            )

        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB."
            )

        with open(filepath, "wb") as f:
            f.write(contents)

        logger.info(f"Staged satellite image {file.filename} -> {filepath} ({file_size} bytes)")
        return image_id, filepath, file_size

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving uploaded file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )


@router.post("/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Upload a single satellite image (GeoTIFF, TIFF, PNG, JPEG).
    Validates format, stages locally, saves record to Firestore,
    and optionally uploads to Firebase Cloud Storage.
    """
    image_id, filepath, file_size = validate_and_save_file(file)

    # Save upload record to Firestore
    save_upload_record(
        image_id=image_id,
        filename=file.filename,
        file_size_bytes=file_size,
        content_type=file.content_type or "application/octet-stream",
        saved_path=filepath,
        user_id=user_id
    )

    # Create project in Firestore
    create_project(image_id=image_id, filename=file.filename, user_id=user_id)

    # Upload to Firebase Storage (async — non-blocking failure)
    upload_image_to_storage(image_id, filepath)

    return ImageUploadResponse(
        image_id=image_id,
        filename=file.filename,
        file_size_bytes=file_size,
        content_type=file.content_type or "application/octet-stream",
        saved_path=filepath,
        message="Satellite image uploaded and staged successfully."
    )


@router.post("/upload-pair", response_model=ImagePairUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_pair(
    before_file: UploadFile = File(..., description="Pre-event satellite image"),
    after_file: UploadFile = File(..., description="Post-event satellite image"),
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Upload a bi-temporal pair of satellite images for change detection.
    """
    pair_id = str(uuid.uuid4())
    logger.info(f"Processing bi-temporal upload pair [Pair ID: {pair_id}]")

    before_id, before_path, before_size = validate_and_save_file(before_file)
    after_id, after_path, after_size = validate_and_save_file(after_file)

    # Save both records to Firestore
    save_upload_record(before_id, before_file.filename, before_size,
                       before_file.content_type or "image/tiff", before_path, user_id)
    save_upload_record(after_id, after_file.filename, after_size,
                       after_file.content_type or "image/tiff", after_path, user_id)

    before_resp = ImageUploadResponse(
        image_id=before_id, filename=before_file.filename,
        file_size_bytes=before_size,
        content_type=before_file.content_type or "application/octet-stream",
        saved_path=before_path, message="Pre-event image staged."
    )
    after_resp = ImageUploadResponse(
        image_id=after_id, filename=after_file.filename,
        file_size_bytes=after_size,
        content_type=after_file.content_type or "application/octet-stream",
        saved_path=after_path, message="Post-event image staged."
    )

    return ImagePairUploadResponse(
        pair_id=pair_id,
        before_image=before_resp,
        after_image=after_resp,
        message="Bi-temporal image pair uploaded and staged successfully."
    )
