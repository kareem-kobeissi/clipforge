import json
import subprocess
from pathlib import Path


def get_video_metadata(file_path: str) -> dict:
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        file_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    video_stream = next(
        (
            stream
            for stream in data["streams"]
            if stream.get("codec_type") == "video"
        ),
        None,
    )

    if video_stream is None:
        raise ValueError("No video stream found.")

    width = int(video_stream["width"])
    height = int(video_stream["height"])

    fps_raw = video_stream.get("avg_frame_rate", "0/1")
    numerator, denominator = fps_raw.split("/")
    fps = (
        float(numerator) / float(denominator)
        if float(denominator) != 0
        else 0
    )

    duration = float(
        data.get("format", {}).get("duration", 0)
    )

    aspect_ratio = width / height if height else 0

    return {
        "filename": Path(file_path).name,
        "width": width,
        "height": height,
        "duration": round(duration, 2),
        "fps": round(fps, 2),
        "codec": video_stream.get("codec_name"),
        "aspect_ratio": round(aspect_ratio, 3),
        "is_horizontal": width > height,
        "is_roughly_16_9": 1.70 <= aspect_ratio <= 1.85,
    }