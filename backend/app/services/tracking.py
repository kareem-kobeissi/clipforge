import cv2


def track_primary_face(
    file_path: str,
    start: float,
    end: float,
    sample_every_frames: int = 10,
) -> dict:
    cap = cv2.VideoCapture(file_path)

    if not cap.isOpened():
        raise ValueError("Could not open video.")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        raise ValueError("Invalid video FPS.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    start_frame = int(start * fps)
    end_frame = int(end * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )

    detections = []

    frame_number = start_frame

    while frame_number <= end_frame:
        success, frame = cap.read()

        if not success:
            break

        if (frame_number - start_frame) % sample_every_frames == 0:
            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY,
            )

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
            )

            if len(faces) > 0:
                
                x, y, w, h = max(
                    faces,
                    key=lambda face: face[2] * face[3],
                )

                center_x = x + (w / 2)
                center_y = y + (h / 2)

                detections.append(
                    {
                        "time": round(frame_number / fps, 2),
                        "center_x": round(center_x, 2),
                        "center_y": round(center_y, 2),
                        "face_width": int(w),
                        "face_height": int(h),
                    }
                )

        frame_number += 1

    cap.release()

    if detections:
        average_center_x = sum(
            item["center_x"]
            for item in detections
        ) / len(detections)

        average_center_y = sum(
            item["center_y"]
            for item in detections
        ) / len(detections)
    else:
       
        average_center_x = width / 2
        average_center_y = height / 2

    return {
        "video_width": width,
        "video_height": height,
        "fps": round(fps, 2),
        "detections_count": len(detections),
        "average_center_x": round(average_center_x, 2),
        "average_center_y": round(average_center_y, 2),
        "detections": detections,
    }