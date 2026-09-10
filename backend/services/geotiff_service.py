import os
import glob
from typing import Dict, Any, Optional
from PIL import Image
import rasterio
from rasterio.warp import transform_bounds

from schemas.metadata_schema import MetadataResponse, GeoBoundingBox
from utils.logger import logger

def locate_image_path(image_id: str, upload_dir: str = "uploads") -> str:
    """
    Finds local file path corresponding to an image_id in uploads directory.
    """
    pattern = os.path.join(upload_dir, f"{image_id}_*")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No satellite image found for image_id: '{image_id}'")
    return matches[0]

def extract_geotiff_metadata(image_id: str, upload_dir: str = "uploads") -> MetadataResponse:
    """
    Extracts spatial, spectral, and acquisition metadata from GeoTIFF or standard raster files.
    """
    filepath = locate_image_path(image_id, upload_dir)
    filename = os.path.basename(filepath)
    # Remove prefix image_id_
    original_filename = "_".join(filename.split("_")[1:]) if "_" in filename else filename

    logger.info(f"Extracting GeoTIFF metadata for file: {filepath}")

    # Check if file can be opened by rasterio
    try:
        with rasterio.open(filepath) as src:
            width = src.width
            height = src.height
            band_count = src.count
            driver = src.driver
            crs_str = str(src.crs) if src.crs else None
            res = list(src.res) if src.res else None
            raw_tags = dict(src.tags())

            # Spatial Bounding Box in WGS84 (EPSG:4326) Lat/Lon
            bbox = None
            if src.crs and src.bounds:
                try:
                    wgs84_bounds = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
                    bbox = GeoBoundingBox(
                        min_lon=round(wgs84_bounds[0], 6),
                        min_lat=round(wgs84_bounds[1], 6),
                        max_lon=round(wgs84_bounds[2], 6),
                        max_lat=round(wgs84_bounds[3], 6)
                    )
                except Exception as ex:
                    logger.warning(f"Could not reproject bounding box to EPSG:4326: {ex}")
                    bbox = GeoBoundingBox(
                        min_lon=round(src.bounds.left, 6),
                        min_lat=round(src.bounds.bottom, 6),
                        max_lon=round(src.bounds.right, 6),
                        max_lat=round(src.bounds.top, 6)
                    )

            # Metadata tags extraction
            acquisition_date = (
                raw_tags.get("ACQUISITION_DATE") or 
                raw_tags.get("TIFFTAG_DATETIME") or 
                raw_tags.get("DATE_ACQUIRED") or 
                None
            )

            satellite_name = (
                raw_tags.get("SATELLITE") or 
                raw_tags.get("SPACECRAFT_NAME") or 
                raw_tags.get("PLATFORM") or 
                None
            )

            # Infer satellite name from filename if missing
            fn_upper = filename.upper()
            if not satellite_name:
                if "SENTINEL-2" in fn_upper or "S2" in fn_upper:
                    satellite_name = "Sentinel-2"
                elif "SENTINEL-1" in fn_upper or "S1" in fn_upper:
                    satellite_name = "Sentinel-1 (SAR)"
                elif "LANDSAT" in fn_upper or "LC08" in fn_upper:
                    satellite_name = "Landsat-8/9"
                elif "CARTOSAT" in fn_upper:
                    satellite_name = "Cartosat-3"
                elif "RISAT" in fn_upper:
                    satellite_name = "RISAT-1A (SAR)"

            # Infer image type (Optical vs SAR)
            image_type = "Optical"
            if satellite_name and "SAR" in satellite_name.upper():
                image_type = "SAR"
            elif any(pol in fn_upper for pol in ["_HH_", "_HV_", "_VV_", "_VH_"]):
                image_type = "SAR"

            band_descriptions = []
            for i in range(1, band_count + 1):
                desc = src.descriptions[i - 1] if src.descriptions and src.descriptions[i - 1] else f"Band {i}"
                band_descriptions.append(desc)

            return MetadataResponse(
                image_id=image_id,
                filename=original_filename,
                is_geotiff=bool(src.crs),
                width=width,
                height=height,
                band_count=band_count,
                driver=driver,
                crs=crs_str,
                resolution=res,
                bounding_box=bbox,
                acquisition_date=acquisition_date,
                satellite_name=satellite_name or "Unknown Satellite Sensor",
                image_type=image_type,
                band_descriptions=band_descriptions,
                raw_tags=raw_tags
            )

    except rasterio.errors.RasterioIOError:
        # Fallback to standard Pillow (for PNG/JPEG images without GIS geospatial headers)
        logger.info(f"File {filepath} is standard raster image (non-GeoTIFF). Using PIL fallback.")
        with Image.open(filepath) as img:
            width, height = img.size
            bands = len(img.getbands())
            driver = img.format or "RASTER"

            return MetadataResponse(
                image_id=image_id,
                filename=original_filename,
                is_geotiff=False,
                width=width,
                height=height,
                band_count=bands,
                driver=driver,
                crs=None,
                resolution=None,
                bounding_box=None,
                acquisition_date=None,
                satellite_name="Standard Optical Image",
                image_type="Optical",
                band_descriptions=[f"Band {b}" for b in img.getbands()],
                raw_tags={}
            )
