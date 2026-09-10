from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ImageUploadResponse(BaseModel):
    image_id: str = Field(..., description="Unique identification token for uploaded satellite image")
    filename: str = Field(..., description="Original filename uploaded by client")
    file_size_bytes: int = Field(..., description="Size of uploaded file in bytes")
    content_type: str = Field(..., description="MIME type of uploaded file")
    saved_path: str = Field(..., description="Local server path where image is staged")
    message: str = Field(..., description="Status message detailing upload success")

class ImagePairUploadResponse(BaseModel):
    pair_id: str = Field(..., description="Unique identification token for image pair session")
    before_image: ImageUploadResponse = Field(..., description="Uploaded pre-event image metadata")
    after_image: ImageUploadResponse = Field(..., description="Uploaded post-event image metadata")
    message: str = Field(..., description="Status message detailing bi-temporal upload success")
