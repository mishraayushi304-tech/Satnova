import os
import glob
from fastapi import APIRouter, HTTPException, status, Header
from fastapi.responses import FileResponse
from typing import Optional

from schemas.report_schema import ReportGenerateRequest, ReportGenerateResponse
from services.report_service import generate_isro_report
from utils.logger import logger

router = APIRouter(tags=["ISRO PDF Reports"])

REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _find_report_file(report_id: str) -> Optional[str]:
    """Finds the local PDF file path for a given report_id."""
    clean_id = report_id[:8].upper()
    exact_pattern = os.path.join(REPORTS_DIR, f"SatNova_Report_{clean_id}*.pdf")
    matches = glob.glob(exact_pattern)
    if not matches:
        matches = glob.glob(os.path.join(REPORTS_DIR, f"SatQuery_Report_{clean_id}*.pdf"))
    if matches:
        return matches[0]

    # Fallback search for any file containing report_id
    fallback = glob.glob(os.path.join(REPORTS_DIR, f"*{report_id}*.pdf"))
    return fallback[0] if fallback else None


@router.post("/report", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/report/generate", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportGenerateRequest,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Generate an official, publication-grade ISRO Intelligence PDF Report.
    Embeds geospatial metadata, LangGraph AI query findings, and analytical charts.
    """
    logger.info(f"[ReportAPI] Generating ISRO PDF report for image_id='{request.image_id}'")

    result = generate_isro_report(
        image_id=request.image_id,
        query=request.query or "Comprehensive Satellite Imagery Intelligence Analysis",
        pair_id=request.pair_id,
        project_id=request.project_id,
        custom_notes=request.custom_notes,
        include_charts=request.include_charts,
        user_id=user_id
    )

    if result.get("error") == "IMAGE_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target satellite image with ID '{request.image_id}' not found. Please upload the image first."
        )

    return ReportGenerateResponse(
        report_id=result["report_id"],
        report_filename=result["report_filename"],
        image_id=result["image_id"],
        task=result["task"],
        download_url=result["download_url"],
        view_url=result["view_url"],
        generated_at=result["generated_at"],
        firebase_url=result.get("firebase_url"),
        message=result["message"]
    )


@router.get("/report/download/{report_id}")
async def download_report(report_id: str):
    """
    Download the generated ISRO PDF report as an attachment.
    """
    pdf_path = _find_report_file(report_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found. It may have expired or been deleted."
        )

    filename = os.path.basename(pdf_path)
    logger.info(f"[ReportAPI] Downloading report: {filename}")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/report/view/{report_id}")
async def view_report(report_id: str):
    """
    View the generated ISRO PDF report inline inside the browser.
    """
    pdf_path = _find_report_file(report_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found."
        )

    filename = os.path.basename(pdf_path)
    logger.info(f"[ReportAPI] Viewing inline report: {filename}")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )
