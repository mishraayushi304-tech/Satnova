from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from schemas.metadata_schema import ImageValidationResult
from services.validation_service import validate_image_pair
from utils.logger import logger

router = APIRouter(tags=["Bi-Temporal Image Comparison"])

class CompareRequest(BaseModel):
    before_image_id: str = Field(..., description="Uploaded pre-event image ID")
    after_image_id: str = Field(..., description="Uploaded post-event image ID")

class CompareResponse(BaseModel):
    pair_id: str = Field(..., description="Comparison session ID")
    validation_result: ImageValidationResult = Field(..., description="Compatibility validation summary")
    status: str = Field(..., description="Status of image pair compatibility check")

@router.post("/compare", response_model=CompareResponse)
async def compare_images(request: CompareRequest):
    """
    Validates compatibility between two satellite images for bi-temporal comparison or change detection.
    Checks spatial bounding overlap, CRS compatibility, dimensions, and optical/SAR modalities.
    """
    logger.info(f"Received bi-temporal comparison request: {request.before_image_id} vs {request.after_image_id}")
    
    validation_result = validate_image_pair(request.before_image_id, request.after_image_id)
    
    if not validation_result.is_valid:
        logger.warning(f"Image pair comparison validation failed: {validation_result.errors}")
        return CompareResponse(
            pair_id=f"pair_{request.before_image_id[:8]}_{request.after_image_id[:8]}",
            validation_result=validation_result,
            status="INCOMPATIBLE"
        )
    
    return CompareResponse(
        pair_id=f"pair_{request.before_image_id[:8]}_{request.after_image_id[:8]}",
        validation_result=validation_result,
        status="READY_FOR_CHANGE_DETECTION"
    )
