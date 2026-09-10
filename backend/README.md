# 🛰️ SatQuery AI Backend (ISRO SIH PS-167)

> **Autonomous Multi-Modal Satellite Imagery Intelligence Platform**  
> *Smart India Hackathon 2026 | Problem Statement PS-167 (ISRO)*

---

## 🌟 Overview

**SatQuery AI** is a production-ready, asynchronous FastAPI backend designed to empower disaster response teams, urban planners, and earth observation scientists at ISRO to analyze complex satellite imagery using plain natural language queries.

It combines:
- **Rasterio & GDAL**: High-precision GeoTIFF spatial metadata extraction (CRS, GSD resolution, bounding coordinates).
- **LangGraph Agentic Orchestrator**: Intelligent routing engine connecting queries to specialized AI models (GeoChat, Qwen2-VL, GroundingDINO, SAM2, and Open-CD).
- **Automated ISRO PDF Reporting**: Publication-grade intelligence reports compiled in seconds with embedded Matplotlib analytics.
- **Firebase Persistence**: Cloud sync for Firestore project history and Cloud Storage persistence with full graceful local offline fallback.
- **Security Hardening**: Standard security headers, filename sanitization, and 0-byte file defense.

---

## 🏗️ Tech Stack

- **Backend Framework**: Python 3.11+, FastAPI 0.110, Uvicorn
- **Geospatial & Image Processing**: Rasterio, Pillow, NumPy, OpenCV
- **AI Agent Orchestration**: LangGraph, LangChain, HuggingFace Transformers
- **Database & Storage**: Firebase Firestore & Cloud Storage (with Offline Mode)
- **Reporting & Visual Analytics**: ReportLab 4.1, Matplotlib 3.8
- **Testing & Quality Assurance**: Pytest (35 automated tests passing)

---

## 📁 Directory Structure

```text
backend/
├── api/
│   └── routers/                 # FastAPI Router Endpoints
│       ├── health.py            # GET  /health
│       ├── upload.py            # POST /upload, POST /upload-pair
│       ├── metadata.py          # GET  /metadata/{image_id}
│       ├── compare.py           # POST /compare
│       ├── query.py             # POST /query, GET /chat-history/{id}
│       ├── projects.py          # GET  /projects
│       └── report.py            # POST /report/generate, GET /report/download, GET /report/view
├── services/                    # Business Logic & Model Service Layer
│   ├── geotiff_service.py       # Rasterio GeoTIFF metadata extractor
│   ├── validation_service.py    # Spatial overlap & CRS compatibility checker
│   ├── task_classifier.py       # Keyword-based natural language intent classifier
│   ├── langgraph_router.py      # LangGraph state machine & AI orchestrator
│   ├── qwen_service.py          # GeoChat captioning & Qwen2-VL VQA engine
│   ├── sam_service.py           # GroundingDINO detection & SAM2 segmentation
│   ├── change_service.py        # Open-CD bi-temporal change detection engine
│   ├── chart_service.py         # Headless Matplotlib analytical chart generator
│   └── report_service.py        # ReportLab ISRO PDF report compilation engine
├── schemas/                     # Pydantic v2 Request & Response Data Contracts
│   ├── upload_schema.py
│   ├── metadata_schema.py
│   ├── query_schema.py
│   └── report_schema.py
├── middleware/                  # Security & Logging Middlewares
│   └── security.py              # X-Content-Type-Options, X-Frame-Options, XSS defense
├── firebase/                    # Cloud Database & Storage Layer
│   ├── config.py                # Graceful offline-first Firebase Admin initializer
│   ├── firestore_service.py     # Collections: uploads, projects, chat_history, reports
│   └── storage_service.py       # Cloud Storage blob uploader
├── tests/                       # Pytest Suite (35 Unit & Integration Tests)
│   ├── test_health.py
│   ├── test_upload.py
│   ├── test_metadata.py
│   ├── test_query.py
│   ├── test_firebase.py
│   ├── test_report.py
│   └── test_hardening.py
├── reports/                     # Local directory for generated ISRO PDF reports
├── uploads/                     # Staging directory for uploaded satellite imagery
├── logs/                        # Rolling execution logs (satquery.log)
├── main.py                      # FastAPI application entrypoint & lifespan
├── SatQuery_AI.postman_collection.json # 1-Click Importable Postman Collection
├── API_DOCUMENTATION.md         # Full API reference catalog
└── HACKATHON_PITCH_GUIDE.md     # 5-Minute ISRO SIH judge presentation script
```

---

## ⚡ Quickstart

### 1. Start the Server
```powershell
cd backend
python main.py
```
*Server starts at: `http://localhost:8000`*

### 2. Interactive Swagger UI Documentation
Open your browser to: **`http://localhost:8000/docs`**

### 3. Run Automated Tests
```powershell
cd backend
python -m pytest tests/
```
Output: **`35 passed in ~12s`** ✅

---

## 🚀 Postman Testing (1-Click)
Import [`SatQuery_AI.postman_collection.json`](./SatQuery_AI.postman_collection.json) directly into Postman. It includes pre-configured variables and automated token chaining!

---

## 📄 Hackathon Pitch Guide
Review [`HACKATHON_PITCH_GUIDE.md`](./HACKATHON_PITCH_GUIDE.md) for the complete 5-minute presentation script, live demo sequence, and answers to judge Q&A!
