from typing import Dict, Any, Tuple
from schemas.metadata_schema import MetadataResponse, ImageValidationResult
from services.geotiff_service import extract_geotiff_metadata
from utils.logger import logger

def validate_single_image(image_id: str, upload_dir: str = "uploads") -> Tuple[MetadataResponse, ImageValidationResult]:
    """
    Validates a single uploaded satellite image for file corruption, valid dimensions, and valid headers.
    """
    errors = []
    warnings = []

    try:
        metadata = extract_geotiff_metadata(image_id, upload_dir)
    except FileNotFoundError as e:
        return None, ImageValidationResult(
            is_valid=False,
            errors=[str(e)],
            warnings=[],
            compatibility_summary={"status": "FILE_NOT_FOUND"}
        )
    except Exception as e:
        logger.error(f"Image corruption error for image_id {image_id}: {str(e)}")
        return None, ImageValidationResult(
            is_valid=False,
            errors=[f"Corrupted or unreadable image file: {str(e)}"],
            warnings=[],
            compatibility_summary={"status": "FILE_CORRUPTED"}
        )

    if metadata.width <= 0 or metadata.height <= 0:
        errors.append("Invalid image dimensions (width or height is 0).")

    if metadata.band_count <= 0:
        errors.append("Invalid image band count (0 bands found).")

    if not metadata.is_geotiff:
        warnings.append("Image lacks GeoTIFF geographic CRS headers. Spatial coordinates will be unanchored.")

    is_valid = len(errors) == 0

    return metadata, ImageValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        compatibility_summary={
            "image_id": image_id,
            "dimensions": f"{metadata.width}x{metadata.height}",
            "is_geotiff": metadata.is_geotiff,
            "crs": metadata.crs or "N/A"
        }
    )

def validate_image_pair(before_id: str, after_id: str, upload_dir: str = "uploads") -> ImageValidationResult:
    """
    Validates compatibility between two satellite images for bi-temporal change detection or comparison.
    Checks spatial overlap, CRS match, dimensions, and optical/SAR modality.
    """
    logger.info(f"Validating image pair compatibility: Before '{before_id}' vs After '{after_id}'")

    meta_before, val_before = validate_single_image(before_id, upload_dir)
    if not val_before.is_valid:
        return ImageValidationResult(
            is_valid=False,
            errors=[f"Pre-event image invalid: {err}" for err in val_before.errors],
            warnings=val_before.warnings
        )

    meta_after, val_after = validate_single_image(after_id, upload_dir)
    if not val_after.is_valid:
        return ImageValidationResult(
            is_valid=False,
            errors=[f"Post-event image invalid: {err}" for err in val_after.errors],
            warnings=val_after.warnings
        )

    errors = []
    warnings = []

    # 1. CRS Matching Check
    if meta_before.is_geotiff and meta_after.is_geotiff:
        if meta_before.crs != meta_after.crs:
            warnings.append(
                f"Different Coordinate Reference Systems detected ({meta_before.crs} vs {meta_after.crs}). "
                "Backend will auto-reproject prior to change detection."
            )

        # 2. Spatial Overlap Check
        b1 = meta_before.bounding_box
        b2 = meta_after.bounding_box
        if b1 and b2:
            # Check bounding box intersection
            has_overlap = not (
                b1.max_lon < b2.min_lon or 
                b1.min_lon > b2.max_lon or 
                b1.max_lat < b2.min_lat or 
                b1.min_lat > b2.max_lat
            )
            if not has_overlap:
                errors.append("These images cannot be compared because they belong to completely different geographic locations.")

    # 3. Dimension Compatibility Check
    if (meta_before.width, meta_before.height) != (meta_after.width, meta_after.height):
        warnings.append(
            f"Image dimensions differ ({meta_before.width}x{meta_before.height} vs {meta_after.width}x{meta_after.height}). "
            "Images will be resampled to matching grid."
        )

    # 4. Modality Check (Optical vs SAR)
    if meta_before.image_type != meta_after.image_type:
        warnings.append(
            f"Cross-modality pair detected ({meta_before.image_type} vs {meta_after.image_type}). "
            "Optical-SAR fusion workflow will be routed."
        )

    is_valid = len(errors) == 0

    return ImageValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        compatibility_summary={
            "spatial_overlap": len(errors) == 0,
            "crs_before": meta_before.crs,
            "crs_after": meta_after.crs,
            "dimensions_before": f"{meta_before.width}x{meta_before.height}",
            "dimensions_after": f"{meta_after.width}x{meta_after.height}",
            "modality": f"{meta_before.image_type} / {meta_after.image_type}"
        }
    )
