from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ReportGenerateRequest(BaseModel):
    image_id: str = Field(..., description="Unique ID of the uploaded satellite image")
    query: Optional[str] = Field(
        default="Comprehensive Satellite Imagery Intelligence Analysis",
        description="Query or instruction to run analysis for before generating the report"
    )
    pair_id: Optional[str] = Field(
        default=None,
        description="Optional bi-temporal pair ID for change detection reports"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Optional Firestore project ID to link the report to"
    )
    custom_notes: Optional[str] = Field(
        default=None,
        description="Optional analyst remarks or mission notes to include in the PDF"
    )
    include_charts: bool = Field(
        default=True,
        description="Whether to generate and embed analytical charts in the PDF"
    )


class ReportGenerateResponse(BaseModel):
    report_id: str = Field(..., description="Unique identifier for the generated PDF report")
    report_filename: str = Field(..., description="Filename of the saved PDF report")
    image_id: str = Field(..., description="Satellite image ID referenced in the report")
    task: str = Field(..., description="AI analytical task performed")
    download_url: str = Field(..., description="Endpoint to download the PDF report")
    view_url: str = Field(..., description="Endpoint to view the PDF inline in browser")
    generated_at: str = Field(..., description="ISO 8601 timestamp of report generation")
    firebase_url: Optional[str] = Field(
        default=None,
        description="Cloud Storage public URL if Firebase is connected"
    )
    message: str = Field(..., description="Status summary message")
