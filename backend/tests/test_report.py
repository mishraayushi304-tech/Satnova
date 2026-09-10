import pytest
from fastapi.testclient import TestClient
import sys
import os
import io
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def create_test_image_bytes() -> bytes:
    img = Image.new('RGB', (100, 100), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def upload_test_image() -> str:
    img_bytes = create_test_image_bytes()
    resp = client.post("/upload", files={"file": ("isro_scene.png", io.BytesIO(img_bytes), "image/png")})
    assert resp.status_code == 201
    return resp.json()["image_id"]


def test_generate_report_success():
    """POST /report/generate should compile an ISRO PDF and return 201."""
    image_id = upload_test_image()
    resp = client.post("/report/generate", json={
        "image_id": image_id,
        "query": "Describe this satellite image and assess coverage.",
        "include_charts": True,
        "custom_notes": "Ground truthing confirmed by Regional Remote Sensing Centre."
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "report_id" in data
    assert data["report_filename"].endswith(".pdf")
    assert "/report/download/" in data["download_url"]
    assert "/report/view/" in data["view_url"]
    assert data["image_id"] == image_id


def test_generate_report_flood_analysis():
    """POST /report/generate should handle flood analysis and embed flood analytics."""
    image_id = upload_test_image()
    resp = client.post("/report/generate", json={
        "image_id": image_id,
        "query": "Detect flooded areas and inundation levels.",
        "include_charts": True
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task"] == "flood"
    assert "report_id" in data


def test_download_report_success():
    """GET /report/download/{report_id} should return valid application/pdf binary content."""
    image_id = upload_test_image()
    gen_resp = client.post("/report/generate", json={
        "image_id": image_id,
        "query": "Analyze vegetation density.",
        "include_charts": True
    })
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    download_resp = client.get(f"/report/download/{report_id}")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert len(download_resp.content) > 1000  # Non-trivial PDF size
    assert download_resp.content[:4] == b"%PDF"  # Standard PDF magic header


def test_view_report_success():
    """GET /report/view/{report_id} should return PDF with inline display disposition."""
    image_id = upload_test_image()
    gen_resp = client.post("/report/generate", json={
        "image_id": image_id,
        "query": "Identify high-risk change zones.",
        "include_charts": True
    })
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    view_resp = client.get(f"/report/view/{report_id}")
    assert view_resp.status_code == 200
    assert view_resp.headers["content-type"] == "application/pdf"
    assert "inline" in view_resp.headers.get("content-disposition", "")
    assert view_resp.content[:4] == b"%PDF"


def test_generate_report_image_not_found():
    """POST /report/generate with invalid image_id should return 404."""
    resp = client.post("/report/generate", json={
        "image_id": "nonexistent_satellite_image_12345",
        "query": "Describe this image."
    })
    assert resp.status_code == 404


def test_download_report_not_found():
    """GET /report/download/{report_id} with invalid ID should return 404."""
    resp = client.get("/report/download/invalid_report_xyz_99999")
    assert resp.status_code == 404
