import subprocess
from pathlib import Path

import cv2
import numpy as np


def _build_tracking_points(
    detections: list[dict],
    video_width: int,
) -> list[tuple[float, float]]:
    if not detections:
        return []

    xs = [item["center_x"] for item in detections]
    median_x = float(np.median(xs))

    # Remove extreme detections that are probably false positives.
    max_distance = video_width * 0.30

    filtered = [
        item
        for item in detections
        if abs(item["center_x"] - median_x) <= max_distance
    ]

    if not filtered:
        filtered = detections

    return [
        (
            float(item["time"]),
            float(item["center_x"]),
        )
        for item in filtered
    ]


def _target_x_for_time(
    current_time: float,
    points: list[tuple[float, float]],
    fallback_x: float,
) -> float:
    if not points:
        return fallback_x

    if current_time <= points[0][0]:
        return points[0][1]

    if current_time >= points[-1][0]:
        return points[-1][1]

    for i in range(len(points) - 1):
        time_a, x_a = points[i]
        time_b, x_b = points[i + 1]

        if time_a <= current_time <= time_b:
            if time_b == time_a:
                return x_a

            progress = (
                current_time - time_a
            ) / (
                time_b - time_a
            )

            return x_a + (
                (x_b - x_a) * progress
            )

    return fallback_x


def create_dynamic_vertical_clip(
    input_path: str,
    output_path: str,
    start: float,
    end: float,
    detections: list[dict],
) -> str:

    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise ValueError("Could not open source video.")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        cap.release()
        raise ValueError("Invalid source video FPS.")

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    crop_width = int(
        height * 9 / 16
    )

    if crop_width % 2 != 0:
        crop_width -= 1

    start_frame = int(start * fps)
    end_frame = int(end * fps)

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        start_frame,
    )

    tracking_points = _build_tracking_points(
        detections,
        width,
    )

    # Start at center or first detected position.
    if tracking_points:
        smoothed_x = tracking_points[0][1]
    else:
        smoothed_x = width / 2

    output = Path(output_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_video = output.with_name(
        output.stem + "_temp.mp4"
    )

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(temp_video),
        fourcc,
        fps,
        (1080, 1920),
    )

    if not writer.isOpened():
        cap.release()
        raise ValueError(
            "Could not create temporary video."
        )

    frame_number = start_frame

    # Lower value = smoother/slower camera movement.
    smoothing = 0.08

    while frame_number <= end_frame:
        success, frame = cap.read()

        if not success:
            break

        current_time = frame_number / fps

        target_x = _target_x_for_time(
            current_time,
            tracking_points,
            width / 2,
        )

        # Smooth movement instead of jumping instantly.
        smoothed_x = (
            smoothing * target_x
            + (1 - smoothing) * smoothed_x
        )

        crop_x = int(
            smoothed_x - crop_width / 2
        )

        crop_x = max(
            0,
            min(
                crop_x,
                width - crop_width,
            ),
        )

        cropped = frame[
            0:height,
            crop_x:crop_x + crop_width,
        ]

        vertical = cv2.resize(
            cropped,
            (1080, 1920),
            interpolation=cv2.INTER_AREA,
        )

        writer.write(vertical)

        frame_number += 1

    cap.release()
    writer.release()

    duration = end - start

    # Add audio from the original video and encode final H.264 MP4.
    command = [
    "ffmpeg",
    "-y",
    "-i",
    str(temp_video),
    "-ss",
    str(start),
    "-i",
    input_path,
    "-t",
    str(duration),
    "-map",
    "0:v:0",
    "-map",
    "1:a?",
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "23",
    "-threads",
    "2",
    "-c:a",
    "aac",
    "-b:a",
    "128k",
    "-pix_fmt",
    "yuv420p",
    "-movflags",
    "+faststart",
    "-shortest",
    str(output),
]

    subprocess.run(
        command,
        check=True,
    )

    temp_video.unlink(
        missing_ok=True
    )

    return str(output)