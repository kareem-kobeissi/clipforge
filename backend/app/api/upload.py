import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.video_service import get_video_metadata

router = APIRouter(
    prefix="/api",
    tags=["video-upload"],
)

UPLOAD_DIR = Path("../data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
}


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...)
):
    original_name = file.filename or "video"

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format.",
        )

    safe_filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / safe_filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        metadata = get_video_metadata(str(destination))

        if not metadata["is_horizontal"]:
            destination.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="Video must be horizontal.",
            )

        if not metadata["is_roughly_16_9"]:
            destination.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="Video must be approximately 16:9.",
            )

        return {
            "success": True,
            "message": "Video uploaded successfully.",
            "video_id": destination.stem,
            "stored_filename": safe_filename,
            "original_filename": original_name,
            "metadata": metadata,
        }

    except HTTPException:
        raise

    except Exception as exc:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Could not process video: {str(exc)}",
        )

    finally:
        await file.close()