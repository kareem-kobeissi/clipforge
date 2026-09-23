from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector


MIN_CLIP_DURATION = 8.0
MAX_CLIP_DURATION = 45.0


def _split_long_scene(
    start: float,
    end: float,
) -> list[tuple[float, float]]:
    duration = end - start

    if duration <= MAX_CLIP_DURATION:
        return [(start, end)]

    clips = []
    current_start = start

    while current_start < end:
        current_end = min(
            current_start + MAX_CLIP_DURATION,
            end,
        )

        clips.append(
            (
                current_start,
                current_end,
            )
        )

        current_start = current_end

    return clips


def _merge_short_clips(
    scenes: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if not scenes:
        return []

    merged = []

    for start, end in scenes:
        duration = end - start

        if duration <= 0:
            continue

        if (
            duration < MIN_CLIP_DURATION
            and merged
        ):
            previous_start, previous_end = merged[-1]

            combined_duration = end - previous_start

            if combined_duration <= MAX_CLIP_DURATION:
                merged[-1] = (
                    previous_start,
                    end,
                )
            else:
                merged.append(
                    (
                        start,
                        end,
                    )
                )
        else:
            merged.append(
                (
                    start,
                    end,
                )
            )

    return merged


def detect_scenes(
    file_path: str,
    threshold: float = 27.0,
) -> list[dict]:
    video = open_video(file_path)

    # Capture the real duration before scene detection.
    video_duration = video.duration.get_seconds()

    if video_duration <= 0:
        return []

    scene_manager = SceneManager()

    scene_manager.add_detector(
        ContentDetector(
            threshold=threshold
        )
    )

    scene_manager.detect_scenes(
        video,
        frame_skip=2,
        show_progress=False,
    )

    scene_list = scene_manager.get_scene_list(
        start_in_scene=True
    )

    raw_scenes = []

    for start, end in scene_list:
        start_seconds = start.get_seconds()
        end_seconds = end.get_seconds()

        if end_seconds > start_seconds:
            raw_scenes.append(
                (
                    start_seconds,
                    end_seconds,
                )
            )

    # SceneDetect can occasionally return only a
    # tiny first scene for some codecs/videos.
    # If its coverage is clearly invalid, treat
    # the entire video as one source scene.
    if not raw_scenes:
        raw_scenes = [
            (
                0.0,
                video_duration,
            )
        ]

    else:
        detected_end = raw_scenes[-1][1]

        if detected_end < video_duration * 0.90:
            raw_scenes = [
                (
                    0.0,
                    video_duration,
                )
            ]

    normalized_scenes = []

    for start, end in raw_scenes:
        normalized_scenes.extend(
            _split_long_scene(
                start,
                end,
            )
        )

    normalized_scenes = _merge_short_clips(
        normalized_scenes
    )

    clips = []

    for index, (start, end) in enumerate(
        normalized_scenes,
        start=1,
    ):
        clips.append(
            {
                "clip_id": index,
                "start": round(start, 2),
                "end": round(end, 2),
                "duration": round(
                    end - start,
                    2,
                ),
            }
        )

    return clips