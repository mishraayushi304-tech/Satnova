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
    img = Image.new('RGB', (100, 100), color='green')
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

def test_upload_valid_image():
    file_bytes = create_valid_test_image_bytes()
    file = ("sample_sat.png", io.BytesIO(file_bytes), "image/png")

    response = client.post("/upload", files={"file": file})
    assert response.status_code == 201
    json_data = response.json()
    assert "image_id" in json_data
    assert json_data["filename"] == "sample_sat.png"
    assert json_data["file_size_bytes"] == len(file_bytes)

def test_upload_invalid_extension():
    file = ("malicious.exe", io.BytesIO(b"binary"), "application/octet-stream")
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
