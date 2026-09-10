"""
Day 6 Hardening & Edge-Case Integration Test Suite
--------------------------------------------------
Validates that SatQuery AI handles unexpected, malformed, or malicious
inputs gracefully without server crashes or raw stack trace leaks.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import io
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_security_headers_present():
    """Verify that all standard security headers are attached to responses."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "SAMEORIGIN"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"


def test_upload_zero_byte_file_rejected():
    """Uploading a 0-byte empty file must return 400 Bad Request."""
    empty_file = io.BytesIO(b"")
    resp = client.post("/upload", files={"file": ("empty.png", empty_file, "image/png")})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_upload_unsupported_extension_rejected():
    """Uploading executable, PDF, or shell script must return 400 Bad Request."""
    for bad_name, mime in [("malware.exe", "application/octet-stream"), ("doc.pdf", "application/pdf"), ("script.sh", "text/plain")]:
        resp = client.post("/upload", files={"file": (bad_name, io.BytesIO(b"dummy payload"), mime)})
        assert resp.status_code == 400
        assert "unsupported" in resp.json()["detail"].lower()


def test_upload_filename_path_traversal_sanitized():
    """Path traversal attempt in filename (../../bad.png) must be sanitized."""
    img = Image.new('RGB', (20, 20), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    
    resp = client.post("/upload", files={"file": ("../../escaped.png", io.BytesIO(buf.getvalue()), "image/png")})
    assert resp.status_code == 201
    saved_path = resp.json()["saved_path"]
    assert ".." not in saved_path
    assert os.path.dirname(saved_path).replace("\\", "/").endswith("uploads")


def test_metadata_nonexistent_id():
    """Requesting metadata for nonexistent ID must return 404 Not Found."""
    resp = client.get("/metadata/nonexistent-image-id-99999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_compare_nonexistent_images():
    """Comparing nonexistent images must return status INCOMPATIBLE with error details."""
    resp = client.post("/compare", json={
        "before_image_id": "nonexistent_before_123",
        "after_image_id": "nonexistent_after_456"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INCOMPATIBLE"
    assert data["validation_result"]["is_valid"] is False
    assert len(data["validation_result"]["errors"]) > 0


def test_query_empty_or_whitespace_string():
    """Sending empty or whitespace query must return 400 Bad Request."""
    img = Image.new('RGB', (20, 20), color='green')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    upload_resp = client.post("/upload", files={"file": ("query_test.png", io.BytesIO(buf.getvalue()), "image/png")})
    image_id = upload_resp.json()["image_id"]

    for bad_query in ["", "   ", "\t\n  "]:
        resp = client.post("/query", json={"image_id": image_id, "query": bad_query})
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()


def test_query_nonexistent_image():
    """Sending query with nonexistent image_id must return 404 Not Found."""
    resp = client.post("/query", json={"image_id": "nonexistent-id-000", "query": "Describe this image."})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_report_download_nonexistent_id():
    """Downloading nonexistent report must return 404 Not Found."""
    resp = client.get("/report/download/nonexistent-report-xyz-999")
    assert resp.status_code == 404


def test_report_view_nonexistent_id():
    """Viewing nonexistent report must return 404 Not Found."""
    resp = client.get("/report/view/nonexistent-report-xyz-999")
    assert resp.status_code == 404


def test_cors_preflight_options():
    """OPTIONS pre-flight request must return appropriate CORS headers."""
    resp = client.options("/query", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
