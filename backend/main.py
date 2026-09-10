import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from utils.logger import logger
from firebase.config import initialize_firebase
from middleware.security import SecurityHeadersMiddleware
from api.routers import health, upload, metadata, compare, query, projects, report

# Ensure storage directories exist
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SatNova Backend Services...")
    initialize_firebase()
    yield
    logger.info("SatNova Backend Server shutting down gracefully.")

app = FastAPI(
    title="SatNova Backend API (ISRO PS-167)",
    description=(
        "Production-ready FastAPI backend for Satellite Imagery Querying, "
        "GeoTIFF Metadata Extraction, AI Model Routing via LangGraph, "
        "Bi-Temporal Change Detection, Firebase Integration, and ISRO Report Generation."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Apply Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logger middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration}ms")
    return response

# ─── Register All Routers ─────────────────────────────────────────────────────
app.include_router(health.router)       # GET  /health
app.include_router(upload.router)       # POST /upload, POST /upload-pair
app.include_router(metadata.router)     # GET  /metadata/{image_id}
app.include_router(compare.router)      # POST /compare
app.include_router(query.router)        # POST /query, GET /chat-history/{project_id}
app.include_router(projects.router)     # GET  /projects
app.include_router(report.router)       # POST /report/generate, POST /report, GET /report/download/{id}, GET /report/view/{id}

@app.get("/")
async def root():
    return {
        "project": "SatNova",
        "team_role": "ISRO SIH PS-167 Backend Server",
        "status": "Online",
        "version": "1.0.0",
        "day": "Day 6 — Security Hardening & Edge-Case Testing Active",
        "endpoints": {
            "upload":          "POST /upload",
            "upload_pair":     "POST /upload-pair",
            "metadata":        "GET  /metadata/{image_id}",
            "compare":         "POST /compare",
            "query":           "POST /query",
            "chat_history":    "GET  /chat-history/{project_id}",
            "projects":        "GET  /projects",
            "report_generate": "POST /report/generate",
            "report_download": "GET  /report/download/{report_id}",
            "report_view":     "GET  /report/view/{report_id}",
            "health":          "GET  /health",
            "docs":            "GET  /docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
