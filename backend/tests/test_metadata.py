import pytest
from fastapi.testclient import TestClient
import sys
import os
import io
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def create_valid_test_image_bytes() -> bytes:
    """Generates valid in-memory PNG image bytes for testing."""
    img = Image.new('RGB', (100, 100), color='blue')
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

def test_metadata_extraction_endpoint():
    # 1. First upload a valid test image
    valid_bytes = create_valid_test_image_bytes()
    upload_res = client.post("/upload", files={"file": ("test_meta.png", io.BytesIO(valid_bytes), "image/png")})
    assert upload_res.status_code == 201
    image_id = upload_res.json()["image_id"]

    # 2. Extract metadata
    meta_res = client.get(f"/metadata/{image_id}")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["image_id"] == image_id
    assert meta_data["width"] == 100
    assert meta_data["height"] == 100
    assert meta_data["band_count"] == 3
    assert meta_data["image_type"] == "Optical"

def test_metadata_not_found():
    meta_res = client.get("/metadata/non_existent_image_id_123")
    assert meta_res.status_code == 404
    assert "not found" in meta_res.json()["detail"].lower()

def test_compare_images_endpoint():
    # Upload two valid test images
    valid_bytes = create_valid_test_image_bytes()
    u1 = client.post("/upload", files={"file": ("img1.png", io.BytesIO(valid_bytes), "image/png")}).json()
    u2 = client.post("/upload", files={"file": ("img2.png", io.BytesIO(valid_bytes), "image/png")}).json()

    resp = client.post("/compare", json={
        "before_image_id": u1["image_id"],
        "after_image_id": u2["image_id"]
    })
    assert resp.status_code == 200
    assert "validation_result" in resp.json()
    assert resp.json()["validation_result"]["is_valid"] is True
