from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector


MIN_CLIP_DURATION = 8.0
MAX_CLIP_DURATION = 60.0


def _split_long_scene(
    start: float,
    end: float,
) -> list[tuple[float, float]]:
    duration = end - start

    if duration <= MAX_CLIP_DURATION:
        return [(start, end)]

    clips = []
    current_start = start

    while end - current_start > MAX_CLIP_DURATION:
        current_end = current_start + MAX_CLIP_DURATION

        clips.append(
            (
                current_start,
                current_end,
            )
        )

        current_start = current_end

    if current_start < end:
        clips.append(
            (
                current_start,
                end,
            )
        )

    return clips


def _merge_short_clips(
    scenes: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if not scenes:
        return []

    merged = []

    for start, end in scenes:
        duration = end - start

        if (
            duration < MIN_CLIP_DURATION
            and merged
        ):
            previous_start, _ = merged[-1]

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

    return merged


def detect_scenes(
    file_path: str,
    threshold: float = 27.0,
) -> list[dict]:
    video = open_video(file_path)

    scene_manager = SceneManager()

    scene_manager.add_detector(
        ContentDetector(
            threshold=threshold
        )
    )

    scene_manager.detect_scenes(
        video,
        frame_skip=2,
        show_progress=True,
    )

    scene_list = scene_manager.get_scene_list()

    if not scene_list:
        return []

    raw_scenes = []

    for start, end in scene_list:
        start_seconds = start.get_seconds()
        end_seconds = end.get_seconds()

        raw_scenes.append(
            (
                start_seconds,
                end_seconds,
            )
        )

    normalized_scenes = []

    for start, end in raw_scenes:
        normalized_scenes.extend(
            _split_long_scene(
                start,
                end,
            )
        )

    normalized_scenes = (
        _merge_short_clips(
            normalized_scenes
        )
    )

    clips = []

    for index, (start, end) in enumerate(
        normalized_scenes,
        start=1,
    ):
        clips.append(
            {
                "clip_id": index,
                "start": round(
                    start,
                    2,
                ),
                "end": round(
                    end,
                    2,
                ),
                "duration": round(
                    end - start,
                    2,
                ),
            }
        )

    return clips