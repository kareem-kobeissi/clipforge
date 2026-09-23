from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.clips import router as clips_router
from app.api.export import router as export_router
from app.api.upload import router as upload_router
from app.api.youtube import router as youtube_router


app = FastAPI(
    title="ClipForge API",
    description="Backend API for converting horizontal videos into vertical clips.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(clips_router)
app.include_router(youtube_router)
app.include_router(export_router)


@app.get("/api/status")
def api_status():
    return {
        "name": "ClipForge API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


frontend_dist = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "dist"
)

if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(
            directory=frontend_dist,
            html=True,
        ),
        name="frontend",
    )