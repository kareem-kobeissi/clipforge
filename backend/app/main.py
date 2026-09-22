from app.api.clips import router as clips_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.youtube import router as youtube_router
from app.api.upload import router as upload_router
from app.api.export import router as export_router

app = FastAPI(
    title="ClipForge API",
    description="Backend API for converting horizontal videos into vertical clips.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(clips_router)
app.include_router(youtube_router)
app.include_router(export_router)
@app.get("/")
def root():
    return {
        "name": "ClipForge API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }