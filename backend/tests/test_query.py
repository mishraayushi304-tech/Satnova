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
    img = Image.new('RGB', (100, 100), color='green')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def upload_test_image(filename: str = "test_sat.png") -> str:
    img_bytes = create_test_image_bytes()
    resp = client.post("/upload", files={"file": (filename, io.BytesIO(img_bytes), "image/png")})
    assert resp.status_code == 201
    return resp.json()["image_id"]

def test_query_caption():
    image_id = upload_test_image()
    resp = client.post("/query", json={"image_id": image_id, "query": "Describe this satellite image."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"] == "caption"
    assert "answer" in data
    assert "GeoChat" in data["model_used"]
    assert data["confidence"] > 0

def test_query_vqa():
    image_id = upload_test_image()
    resp = client.post("/query", json={"image_id": image_id, "query": "What is the land use pattern here?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"] == "vqa"
    assert "Qwen2-VL" in data["model_used"]

def test_query_grounding():
    image_id = upload_test_image()
    resp = client.post("/query", json={"image_id": image_id, "query": "Highlight rivers in this image."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"] == "grounding"
    assert "GroundingDINO" in data["model_used"]
    assert "SAM2" in data["model_used"]

def test_query_flood():
    image_id = upload_test_image()
    resp = client.post("/query", json={"image_id": image_id, "query": "Detect flooded areas."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"] == "flood"
    assert data["confidence"] > 0

def test_query_vegetation():
    image_id = upload_test_image()
    resp = client.post("/query", json={"image_id": image_id, "query": "Analyze vegetation in this image."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"] == "vegetation"
    assert data["execution_summary"]["tools"] is not None

def test_query_not_found():
    resp = client.post("/query", json={"image_id": "nonexistent_id_xyz", "query": "Describe this image."})
    assert resp.status_code == 404

def test_query_empty_string():
    image_id = upload_test_image()
    resp = client.post("/query", json={"image_id": image_id, "query": "  "})
    assert resp.status_code == 400
