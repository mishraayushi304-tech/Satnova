from fastapi import APIRouter, HTTPException, status
from schemas.metadata_schema import MetadataResponse
from services.geotiff_service import extract_geotiff_metadata
from utils.logger import logger

router = APIRouter(prefix="/metadata", tags=["Metadata Extraction"])

@router.get("/{image_id}", response_model=MetadataResponse)
async def get_image_metadata(image_id: str):
    """
    Extracts spatial, spectral, coordinate system, and sensor metadata for an uploaded satellite image.
    Acts as the 'Image Passport' for downstream AI routing and analysis.
    """
    try:
        metadata = extract_geotiff_metadata(image_id)
        return metadata
    except FileNotFoundError as e:
        logger.warning(f"Metadata requested for non-existent image_id '{image_id}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID '{image_id}' not found. Please upload the image first."
        )
    except Exception as e:
        logger.error(f"Error extracting metadata for image_id '{image_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract GeoTIFF metadata: {str(e)}"
        )
