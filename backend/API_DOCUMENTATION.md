# 🛰️ SatQuery AI — API Reference & Developer Guide
### ISRO Smart India Hackathon 2026 (Problem Statement PS-167)

**Base URL**: `http://127.0.0.1:8000`  
**Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs` (Swagger UI)  
**Alternative Docs**: `http://127.0.0.1:8000/redoc` (ReDoc)  

---

## 📋 Endpoint Catalog Summary

| Category | Method | Endpoint | Description |
|:---|:---:|:---|:---|
| **System** | `GET` | `/` | Root service status and endpoint index |
| **System** | `GET` | `/health` | Health probe & service uptime check |
| **Ingestion** | `POST` | `/upload` | Single satellite image upload & staging |
| **Ingestion** | `POST` | `/upload-pair` | Bi-temporal image pair upload for change analysis |
| **Metadata** | `GET` | `/metadata/{image_id}` | GeoTIFF spatial, spectral & CRS metadata extraction |
| **Metadata** | `POST` | `/compare` | Image pair spatial bounding & CRS validation |
| **AI Query** | `POST` | `/query` | Natural language satellite query via LangGraph |
| **History** | `GET` | `/chat-history/{id}` | Session Q&A conversation history |
| **Projects** | `GET` | `/projects` | All satellite analysis projects for user |
| **Reports** | `POST` | `/report/generate` | Generate publication-grade ISRO PDF Report |
| **Reports** | `POST` | `/report` | Alias for `/report/generate` |
| **Reports** | `GET` | `/report/view/{id}` | View PDF report inline in browser |
| **Reports** | `GET` | `/report/download/{id}` | Download PDF report as attachment |

---

## 1. System Health & Info

### `GET /`
Returns root server details and endpoint directory.

**Response (200 OK):**
```json
{
  "project": "SatQuery AI",
  "team_role": "ISRO SIH PS-167 Backend Server",
  "status": "Online",
  "version": "1.0.0",
  "day": "Day 6 — Security Hardening & Edge-Case Testing Active",
  "endpoints": { ... }
}
```

### `GET /health`
Liveness probe.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "project": "SatQuery AI",
  "environment": "development"
}
```

---

## 2. Image Ingestion

### `POST /upload`
Uploads a single satellite raster image (`.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`).

**Request (Multipart Form-Data):**
- `file`: Binary file stream
- `X-User-ID` *(Header, Optional)*: User identifier

**Response (201 Created):**
```json
{
  "image_id": "3b89a811-0941-477d-8bd4-523c0429f9ba",
  "filename": "kerala_flood_sentinel2.tif",
  "file_size_bytes": 1048576,
  "content_type": "image/tiff",
  "saved_path": "uploads/3b89a811-..._kerala_flood_sentinel2.tif",
  "message": "Satellite image uploaded and staged successfully."
}
```

---

## 3. Geospatial Metadata Extraction

### `GET /metadata/{image_id}`
Extracts geospatial bounds, coordinate projection (CRS), bands, and spatial resolution.

**Response (200 OK):**
```json
{
  "image_id": "3b89a811-0941-477d-8bd4-523c0429f9ba",
  "filename": "kerala_flood_sentinel2.tif",
  "format": "GTiff",
  "width": 1024,
  "height": 1024,
  "band_count": 4,
  "crs": "EPSG:32643 - WGS 84 / UTM zone 43N",
  "bounding_box": {
    "min_x": 76.215,
    "min_y": 9.925,
    "max_x": 76.350,
    "max_y": 10.050
  },
  "resolution_x": 10.0,
  "resolution_y": 10.0,
  "is_georeferenced": true
}
```

---

## 4. LangGraph AI Query Processing

### `POST /query`
Main multi-modal intelligence endpoint. LangGraph classifies user intent and routes to:
- **GeoChat**: Scene description & captioning
- **Qwen2-VL**: Visual question answering (VQA)
- **GroundingDINO + SAM2**: Prompted feature detection & segmentation
- **Open-CD**: Bi-temporal change detection

**Request Body (JSON):**
```json
{
  "image_id": "3b89a811-0941-477d-8bd4-523c0429f9ba",
  "query": "Detect flooded areas in this image."
}
```

**Response (200 OK):**
```json
{
  "image_id": "3b89a811-0941-477d-8bd4-523c0429f9ba",
  "query": "Detect flooded areas in this image.",
  "task": "flood",
  "answer": "Flood analysis complete. Approximately 34.7% of the region shows inundation. Waterlogged areas concentrated near river delta. Estimated flooded area: 127.4 sq km.",
  "confidence": 93.2,
  "model_used": ["Qwen2-VL", "SAM2"],
  "execution_summary": {
    "image_type": "Sentinel-2 (Optical)",
    "tools": ["Qwen2-VL", "SAM2"],
    "processing_time": "1.32 seconds"
  }
}
```

---

## 5. ISRO PDF Intelligence Reports

### `POST /report/generate` *(or `POST /report`)*
Compiles an official A4 intelligence dossier with embedded Matplotlib analytics.

**Request Body (JSON):**
```json
{
  "image_id": "3b89a811-0941-477d-8bd4-523c0429f9ba",
  "query": "Detect flooded areas and evaluate submerged surface.",
  "include_charts": true,
  "custom_notes": "Ground truthing confirmed by Regional Remote Sensing Centre, Jodhpur."
}
```

**Response (201 Created):**
```json
{
  "report_id": "8f3b2029-7984-4841-b1e9-6f1784917452",
  "report_filename": "SatQuery_Report_8F3B2029.pdf",
  "image_id": "3b89a811-0941-477d-8bd4-523c0429f9ba",
  "task": "flood",
  "download_url": "/report/download/8f3b2029-7984-4841-b1e9-6f1784917452",
  "view_url": "/report/view/8f3b2029-7984-4841-b1e9-6f1784917452",
  "generated_at": "2026-09-07T17:03:00Z",
  "firebase_url": null,
  "message": "ISRO SIH PS-167 Intelligence Report compiled successfully."
}
```

### `GET /report/view/{report_id}`
Renders the generated PDF directly in the browser viewer.

### `GET /report/download/{report_id}`
Downloads the PDF file with `Content-Disposition: attachment`.
