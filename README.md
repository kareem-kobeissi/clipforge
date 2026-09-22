# ClipForge

ClipForge is a local video clipping tool that converts long-form horizontal videos into vertical social media clips.

It accepts uploaded 16:9 video files or YouTube URLs, automatically detects clip boundaries, allows manual timing adjustments, tracks the main subject, converts clips to 9:16 format, and supports individual or bulk export.

## Features

- Upload horizontal 16:9 video files
- Import public YouTube videos
- Automatic scene-based clip detection
- Manual start and end time adjustment
- Clip duration adjustment before export
- Face-based subject tracking
- Dynamic crop movement instead of a fixed center crop
- 16:9 to 9:16 conversion
- 1080 × 1920 vertical MP4 output
- In-browser vertical clip preview
- Individual MP4 download
- Generate and export all clips as a ZIP
- Local video processing
- Responsive web interface

## Tech Stack

### Frontend

- React
- TypeScript
- Vite

### Backend

- Python
- FastAPI
- OpenCV
- PySceneDetect
- yt-dlp
- FFmpeg
- FFprobe

All tools used by the project are free and open source.

## How It Works

### 1. Import Video

The user can either:

- upload a local video file
- paste a public YouTube URL

Uploaded and imported videos are validated before processing.

The current input validation expects approximately 16:9 horizontal video.

### 2. Detect Clips

ClipForge analyzes the full video using PySceneDetect.

Detected scenes are converted into editable clips.

Very short scenes are merged with the previous clip, while very long scenes can be divided into smaller sections to produce more practical clip lengths.

### 3. Adjust Timing

Each detected clip includes editable start and end times.

The user can shorten or extend a clip before generating the vertical version.

The backend validates that:

- the start time is not negative
- the end time is greater than the start time
- the end time does not exceed the source video duration

### 4. Track the Subject

OpenCV is used to detect faces throughout each selected clip.

Detected face positions are sampled over time and used to calculate the horizontal crop position.

The crop position is interpolated and smoothed between detections so that the vertical frame moves gradually instead of jumping between positions.

If no face is detected, ClipForge falls back to a centered crop.

### 5. Generate Vertical Video

The selected clip is converted from horizontal 16:9 format to vertical 9:16 format.

Output resolution:

```text
1080 × 1920
```

The final file is encoded as an H.264 MP4 with AAC audio using FFmpeg.

### 6. Export

Users can:

- download individual generated clips
- preview clips directly in the browser
- export all detected clips together

When Export All is selected, any clips that have not yet been generated are processed first, then all vertical clips are packaged into a ZIP file.

## Project Structure

```text
clipforge/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── clips.py
│   │   │   ├── export.py
│   │   │   ├── upload.py
│   │   │   └── youtube.py
│   │   ├── services/
│   │   │   ├── cropping.py
│   │   │   ├── segmentation.py
│   │   │   ├── tracking.py
│   │   │   └── video_service.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── data/
    ├── uploads/
    ├── clips/
    └── exports/
```

## Requirements

Install the following before running the project:

- Python 3.10+
- Node.js 20+
- npm
- FFmpeg
- FFprobe

Check FFmpeg:

```bash
ffmpeg -version
```

Check FFprobe:

```bash
ffprobe -version
```

## Backend Setup

Open a terminal from the project folder.

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

Open another terminal.

```bash
cd frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

## Basic Usage

1. Start the backend.
2. Start the frontend.
3. Open ClipForge in the browser.
4. Upload a 16:9 video or paste a YouTube URL.
5. Generate clips.
6. Adjust clip start or end times if required.
7. Generate a vertical clip.
8. Preview or download the result.
9. Use Export All to process and download all clips together.

## API Endpoints

### Upload Video

```text
POST /api/upload
```

### Import YouTube Video

```text
POST /api/youtube
```

### Detect Clips

```text
POST /api/segment
```

### Update Clip Timing

```text
POST /api/clips/update
```

### Track Clip Subject

```text
POST /api/clips/track
```

### Generate Vertical Clip

```text
POST /api/clips/vertical
```

### Preview Generated Clip

```text
GET /api/preview/{filename}
```

### Download Generated Clip

```text
GET /api/export/{filename}
```

### Export All Clips

```text
GET /api/export-all/{video_id}
```

## Design Decisions

### Scene Detection

PySceneDetect was used because it provides scene-change detection without requiring a paid API or external cloud service.

A content-based detector is suitable for an MVP, although visual scene changes do not always correspond to semantic topic changes.

### Subject Tracking

The current implementation uses OpenCV Haar face detection.

Face positions are sampled across the selected clip and used to create a moving crop.

Interpolation and smoothing are applied to reduce sudden camera movement.

This keeps the implementation lightweight and fully local.

### Local Processing

Video processing is performed locally rather than sending uploaded video to an external service.

This keeps the MVP simple and avoids paid processing infrastructure.

### YouTube Resolution

YouTube imports are limited to a maximum of 720p to keep local download and processing time manageable.

## Current Limitations

The current version is intended as a working MVP.

The face tracker may lose the subject when:

- the face is turned away from the camera
- the face is very small
- lighting is poor
- several people appear in the same frame
- another detected face becomes larger than the intended subject

A production version could use a stronger person detector combined with persistent object tracking.

Automatic segmentation is based primarily on visual scene changes. A production version could combine scene detection with speech transcription and semantic topic detection.

Video processing currently runs synchronously. For larger-scale deployment, processing jobs could be moved to a background task queue.

Generated media is currently stored on the local filesystem. Production deployment could use persistent object storage.

## Build

To create a frontend production build:

```bash
cd frontend
npm run build
```

## License

This project was created as a technical assessment project.
