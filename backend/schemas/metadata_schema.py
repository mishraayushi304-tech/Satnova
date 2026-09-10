from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GeoBoundingBox(BaseModel):
    min_lat: Optional[float] = Field(None, description="Southernmost latitude coordinate")
    max_lat: Optional[float] = Field(None, description="Northernmost latitude coordinate")
    min_lon: Optional[float] = Field(None, description="Westernmost longitude coordinate")
    max_lon: Optional[float] = Field(None, description="Easternmost longitude coordinate")

class MetadataResponse(BaseModel):
    image_id: str = Field(..., description="Unique image identifier")
    filename: str = Field(..., description="Original filename")
    is_geotiff: bool = Field(..., description="Whether the image contains geographic reference headers")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    band_count: int = Field(..., description="Number of spectral/color bands")
    driver: str = Field(..., description="Raster format driver (e.g. GTiff, PNG, JPEG)")
    crs: Optional[str] = Field(None, description="Coordinate Reference System (e.g. EPSG:4326, EPSG:32643)")
    resolution: Optional[List[float]] = Field(None, description="Pixel resolution [x_res, y_res] in CRS units or meters")
    bounding_box: Optional[GeoBoundingBox] = Field(None, description="Spatial bounding coordinates (Lat/Lon)")
    acquisition_date: Optional[str] = Field(None, description="Acquisition timestamp if present in metadata tags")
    satellite_name: Optional[str] = Field(None, description="Satellite mission name (e.g. Sentinel-2, Landsat-8, Cartosat-3)")
    image_type: str = Field("Optical", description="Image spectral classification (Optical or SAR)")
    band_descriptions: List[str] = Field(default_factory=list, description="Descriptions or color names for each band")
    raw_tags: Dict[str, Any] = Field(default_factory=dict, description="Raw metadata tags embedded in file")

class ImageValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether the image or pair is valid for analysis")
    errors: List[str] = Field(default_factory=list, description="List of blocking validation error messages")
    warnings: List[str] = Field(default_factory=list, description="List of non-blocking warning messages")
    compatibility_summary: Dict[str, Any] = Field(default_factory=dict, description="Detailed comparison details")
