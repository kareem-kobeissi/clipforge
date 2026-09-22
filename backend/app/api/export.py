from pathlib import Path
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/api",
    tags=["export"],
)

CLIPS_DIR = Path("../data/clips")
EXPORTS_DIR = Path("../data/exports")

CLIPS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/preview/{filename}")
def preview_clip(filename: str):
    file_path = CLIPS_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Clip file not found.",
        )

    if file_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=400,
            detail="Only MP4 files can be previewed.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
    )
@router.get("/export/{filename}")
def export_single_clip(filename: str):
    file_path = CLIPS_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Clip file not found.",
        )

    if file_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=400,
            detail="Only MP4 clip files can be exported.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name,
    )


@router.get("/export-all/{video_id}")
def export_all_clips(video_id: str):
    matching_files = sorted(
        CLIPS_DIR.glob(
            f"{video_id}_clip_*_vertical.mp4"
        )
    )

    if not matching_files:
        raise HTTPException(
            status_code=404,
            detail="No generated clips found for this video.",
        )

    zip_filename = f"{video_id}_clips.zip"
    zip_path = EXPORTS_DIR / zip_filename

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for clip_path in matching_files:
            zip_file.write(
                clip_path,
                arcname=clip_path.name,
            )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_filename,
    )