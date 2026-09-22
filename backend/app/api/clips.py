from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.cropping import create_dynamic_vertical_clip
from app.services.segmentation import detect_scenes
from app.services.tracking import track_primary_face
from app.services.video_service import get_video_metadata


router = APIRouter(
    prefix="/api",
    tags=["clips"],
)

UPLOAD_DIR = Path("../data/uploads")


class SegmentRequest(BaseModel):
    stored_filename: str


class ClipUpdateRequest(BaseModel):
    stored_filename: str
    clip_id: int
    start: float
    end: float


class TrackingRequest(BaseModel):
    stored_filename: str
    start: float
    end: float


class VerticalClipRequest(BaseModel):
    stored_filename: str
    clip_id: int
    start: float
    end: float


@router.post("/segment")
def segment_video(payload: SegmentRequest):
    file_path = UPLOAD_DIR / payload.stored_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found.",
        )

    try:
        metadata = get_video_metadata(str(file_path))

        clips = detect_scenes(str(file_path))

        
        if not clips:
            clips = [
                {
                    "clip_id": 1,
                    "start": 0,
                    "end": metadata["duration"],
                    "duration": metadata["duration"],
                }
            ]

        return {
            "success": True,
            "stored_filename": payload.stored_filename,
            "clip_count": len(clips),
            "clips": clips,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not segment video: {str(exc)}",
        )


@router.post("/clips/update")
def update_clip(payload: ClipUpdateRequest):
    file_path = UPLOAD_DIR / payload.stored_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found.",
        )

    metadata = get_video_metadata(str(file_path))
    video_duration = metadata["duration"]

    if payload.start < 0:
        raise HTTPException(
            status_code=400,
            detail="Clip start cannot be negative.",
        )

    if payload.end <= payload.start:
        raise HTTPException(
            status_code=400,
            detail="Clip end must be greater than clip start.",
        )

    if payload.end > video_duration:
        raise HTTPException(
            status_code=400,
            detail="Clip end cannot exceed the video duration.",
        )

    duration = round(payload.end - payload.start, 2)

    return {
        "success": True,
        "message": "Clip timing updated successfully.",
        "clip": {
            "clip_id": payload.clip_id,
            "start": round(payload.start, 2),
            "end": round(payload.end, 2),
            "duration": duration,
        },
        "video_duration": video_duration,
    }


@router.post("/clips/track")
def track_clip_subject(payload: TrackingRequest):
    file_path = UPLOAD_DIR / payload.stored_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found.",
        )

    if payload.start < 0:
        raise HTTPException(
            status_code=400,
            detail="Start cannot be negative.",
        )

    if payload.end <= payload.start:
        raise HTTPException(
            status_code=400,
            detail="End must be greater than start.",
        )

    metadata = get_video_metadata(str(file_path))

    if payload.end > metadata["duration"]:
        raise HTTPException(
            status_code=400,
            detail="End cannot exceed video duration.",
        )

    try:
        tracking = track_primary_face(
            str(file_path),
            payload.start,
            payload.end,
        )

        return {
            "success": True,
            "tracking": tracking,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not track subject: {str(exc)}",
        )


@router.post("/clips/vertical")
def create_vertical_video(payload: VerticalClipRequest):
    file_path = UPLOAD_DIR / payload.stored_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found.",
        )

    metadata = get_video_metadata(str(file_path))

    if payload.start < 0:
        raise HTTPException(
            status_code=400,
            detail="Start cannot be negative.",
        )

    if payload.end <= payload.start:
        raise HTTPException(
            status_code=400,
            detail="End must be greater than start.",
        )

    if payload.end > metadata["duration"]:
        raise HTTPException(
            status_code=400,
            detail="End cannot exceed video duration.",
        )

    try:
        tracking = track_primary_face(
            str(file_path),
            payload.start,
            payload.end,
            sample_every_frames=20,
        )

        output_dir = Path("../data/clips")
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_filename = (
            f"{Path(payload.stored_filename).stem}"
            f"_clip_{payload.clip_id}_vertical.mp4"
        )

        output_path = output_dir / output_filename

        create_dynamic_vertical_clip(
            input_path=str(file_path),
            output_path=str(output_path),
            start=payload.start,
            end=payload.end,
            detections=tracking["detections"],
        )

        return {
            "success": True,
            "message": "Vertical clip created successfully.",
            "clip_id": payload.clip_id,
            "output_filename": output_filename,
            "start": payload.start,
            "end": payload.end,
            "duration": round(
                payload.end - payload.start,
                2,
            ),
            "tracking": {
                "detections_count": tracking["detections_count"],
                "mode": "dynamic_smoothed_tracking",
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not create vertical clip: {str(exc)}",
        )