import re
import uuid
from pathlib import Path

import yt_dlp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.video_service import get_video_metadata


router = APIRouter(
    prefix="/api",
    tags=["youtube"],
)

UPLOAD_DIR = Path("../data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class YouTubeRequest(BaseModel):
    url: str


def is_valid_youtube_url(url: str) -> bool:
    pattern = re.compile(
        r"^(https?://)?(www\.)?"
        r"(youtube\.com/watch\?v=|youtu\.be/)"
        r"[A-Za-z0-9_-]{6,}"
    )
    return bool(pattern.search(url))


@router.post("/youtube")
def download_youtube_video(payload: YouTubeRequest):
    url = payload.url.strip()

    if not is_valid_youtube_url(url):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL.",
        )

    video_id = uuid.uuid4().hex

    output_template = str(
        UPLOAD_DIR / f"{video_id}.%(ext)s"
    )

    ydl_options = {
       "format": "bestvideo[height<=720]+bestaudio/best[height<=720]", 
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(
                url,
                download=True,
            )

        downloaded_file = UPLOAD_DIR / f"{video_id}.mp4"

        if not downloaded_file.exists():
            candidates = list(
                UPLOAD_DIR.glob(f"{video_id}.*")
            )

            if not candidates:
                raise RuntimeError(
                    "Downloaded video file was not found."
                )

            downloaded_file = candidates[0]

        metadata = get_video_metadata(
            str(downloaded_file)
        )

        if not metadata["is_horizontal"]:
            downloaded_file.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="YouTube video must be horizontal.",
            )

        if not metadata["is_roughly_16_9"]:
            downloaded_file.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="YouTube video must be approximately 16:9.",
            )

        return {
            "success": True,
            "message": "YouTube video downloaded successfully.",
            "video_id": video_id,
            "stored_filename": downloaded_file.name,
            "title": info.get("title"),
            "duration": info.get("duration"),
            "webpage_url": info.get("webpage_url"),
            "metadata": metadata,
        }

    except HTTPException:
        raise

    except Exception as exc:
        for file in UPLOAD_DIR.glob(f"{video_id}.*"):
            file.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Could not download YouTube video: {str(exc)}",
        )