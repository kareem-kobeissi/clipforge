import { useState } from "react";
import "./App.css";

type VideoMetadata = {
  width: number;
  height: number;
  duration: number;
  fps: number;
  codec: string;
  aspect_ratio: number;
};

type UploadResponse = {
  success: boolean;
  video_id?: string;
  stored_filename: string;
  original_filename?: string;
  title?: string;
  metadata: VideoMetadata;
};

type Clip = {
  clip_id: number;
  start: number;
  end: number;
  duration: number;
  output_filename?: string;
  generating?: boolean;
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");

  const [video, setVideo] =
    useState<UploadResponse | null>(null);

  const [clips, setClips] = useState<Clip[]>([]);

  const [loading, setLoading] = useState(false);
  const [segmenting, setSegmenting] = useState(false);
  const [exportingAll, setExportingAll] = useState(false);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] =
    useState("");

  const clearMessages = () => {
    setError("");
    setSuccessMessage("");
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);

    return `${mins}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  const uploadVideo = async () => {
    if (!file) {
      setError("Please choose a video file first.");
      return;
    }

    setLoading(true);
    clearMessages();
    setClips([]);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        "http://127.0.0.1:8000/api/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed."
        );
      }

      setVideo(data);
      setSuccessMessage(
        "Video uploaded and validated successfully."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  const importYoutube = async () => {
    if (!youtubeUrl.trim()) {
      setError("Please enter a YouTube URL.");
      return;
    }

    setLoading(true);
    clearMessages();
    setClips([]);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/youtube",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: youtubeUrl,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "YouTube import failed."
        );
      }

      setVideo(data);
      setSuccessMessage(
        "YouTube video imported successfully."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  const generateClips = async () => {
    if (!video) return;

    setSegmenting(true);
    clearMessages();

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/segment",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            stored_filename:
              video.stored_filename,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Could not generate clips."
        );
      }

      setClips(data.clips);

      setSuccessMessage(
        `${data.clips.length} clip${
          data.clips.length === 1 ? "" : "s"
        } detected successfully.`
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not generate clips."
      );
    } finally {
      setSegmenting(false);
    }
  };

  const updateClipValue = (
    clipId: number,
    field: "start" | "end",
    value: number
  ) => {
    setClips((currentClips) =>
      currentClips.map((clip) => {
        if (clip.clip_id !== clipId) {
          return clip;
        }

        const updatedClip = {
          ...clip,
          [field]: value,
        };

        return {
          ...updatedClip,
          duration: Math.max(
            0,
            Number(
              (
                updatedClip.end -
                updatedClip.start
              ).toFixed(2)
            )
          ),
        };
      })
    );
  };

  const saveClipTiming = async (
    clip: Clip
  ) => {
    if (!video) return;

    clearMessages();

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/clips/update",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            stored_filename:
              video.stored_filename,
            clip_id: clip.clip_id,
            start: clip.start,
            end: clip.end,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Could not update clip."
        );
      }

      setClips((currentClips) =>
        currentClips.map((item) =>
          item.clip_id === clip.clip_id
            ? {
                ...item,
                ...data.clip,
              }
            : item
        )
      );

      setSuccessMessage(
        `Clip ${clip.clip_id} timing updated.`
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not update clip."
      );
    }
  };

  const generateVertical = async (
    clip: Clip
  ) => {
    if (!video) return;

    clearMessages();

    setClips((currentClips) =>
      currentClips.map((item) =>
        item.clip_id === clip.clip_id
          ? {
              ...item,
              generating: true,
            }
          : item
      )
    );

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/clips/vertical",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            stored_filename:
              video.stored_filename,
            clip_id: clip.clip_id,
            start: clip.start,
            end: clip.end,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Could not generate vertical clip."
        );
      }

      setClips((currentClips) =>
        currentClips.map((item) =>
          item.clip_id === clip.clip_id
            ? {
                ...item,
                generating: false,
                output_filename:
                  data.output_filename,
              }
            : item
        )
      );

      setSuccessMessage(
        `Clip ${clip.clip_id} converted to vertical successfully.`
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not generate vertical clip."
      );

      setClips((currentClips) =>
        currentClips.map((item) =>
          item.clip_id === clip.clip_id
            ? {
                ...item,
                generating: false,
              }
            : item
        )
      );
    }
  };

  const downloadClip = (
    filename: string
  ) => {
    window.open(
      `http://127.0.0.1:8000/api/export/${filename}`,
      "_blank"
    );
  };

  const exportAll = async () => {
  if (!video || clips.length === 0) return;

  setExportingAll(true);
  clearMessages();

  try {
    const videoId =
      video.video_id ||
      video.stored_filename.split(".")[0];

    /*
      Generate every clip that has not already
      been converted to vertical.
    */
    for (const clip of clips) {
      if (clip.output_filename) {
        continue;
      }

      setClips((currentClips) =>
        currentClips.map((item) =>
          item.clip_id === clip.clip_id
            ? {
                ...item,
                generating: true,
              }
            : item
        )
      );

      const verticalResponse = await fetch(
        "http://127.0.0.1:8000/api/clips/vertical",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            stored_filename:
              video.stored_filename,
            clip_id: clip.clip_id,
            start: clip.start,
            end: clip.end,
          }),
        }
      );

      const verticalData =
        await verticalResponse.json();

      if (!verticalResponse.ok) {
        setClips((currentClips) =>
          currentClips.map((item) =>
            item.clip_id === clip.clip_id
              ? {
                  ...item,
                  generating: false,
                }
              : item
          )
        );

        throw new Error(
          verticalData.detail ||
            `Could not generate Clip ${clip.clip_id}.`
        );
      }

      setClips((currentClips) =>
        currentClips.map((item) =>
          item.clip_id === clip.clip_id
            ? {
                ...item,
                generating: false,
                output_filename:
                  verticalData.output_filename,
              }
            : item
        )
      );
    }

    /*
      After every clip exists, request the ZIP.
    */
    const response = await fetch(
      `http://127.0.0.1:8000/api/export-all/${videoId}`
    );

    if (!response.ok) {
      const data = await response.json();

      throw new Error(
        data.detail ||
          "Could not export all clips."
      );
    }

    const blob = await response.blob();

    const url =
      window.URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download =
      `${videoId}_clips.zip`;

    document.body.appendChild(link);

    link.click();

    link.remove();

    window.URL.revokeObjectURL(url);

    setSuccessMessage(
      `All ${clips.length} clips were generated and exported successfully.`
    );
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Could not export all clips."
    );
  } finally {
    setExportingAll(false);
  }
};



  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <div className="brand-mark">
              <span>CF</span>
            </div>

            <div>
              <div className="brand-name">
                ClipForge
              </div>
              <div className="brand-subtitle">
                AI Video Studio
              </div>
            </div>
          </div>

          <div className="topbar-badge">
            <span className="status-dot" />
            Local processing
          </div>
        </div>
      </header>

      <main className="app">
        <section className="hero">
          <div className="hero-pill">
            <span className="hero-pill-dot" />
            AI CONTENT LAB TOOL
          </div>

          <h1>
            Turn long videos into
            <span> vertical content.</span>
          </h1>

          <p className="subtitle">
            Automatically detect clips, track
            subjects and create social-ready
            9:16 videos — all from one simple
            workspace.
          </p>

          <div className="hero-features">
            <span>16:9 → 9:16</span>
            <span>Subject tracking</span>
            <span>Smart segmentation</span>
            <span>Local processing</span>
          </div>
        </section>

        <section className="workspace-card import-card">
          <div className="card-heading">
            <div className="step-number">01</div>

            <div>
              <p className="section-label">
                SOURCE
              </p>
              <h2>Import your video</h2>
              <p>
                Upload a horizontal video or
                paste a YouTube link.
              </p>
            </div>
          </div>

          <div className="source-grid">
            <div className="source-panel">
              <div className="source-icon">
                ↑
              </div>

              <h3>Upload video</h3>

              <p>
                Choose a 16:9 video from your
                computer.
              </p>

              <label className="file-picker">
                <input
                  type="file"
                  accept="video/*"
                  onChange={(event) =>
                    setFile(
                      event.target.files?.[0] ||
                        null
                    )
                  }
                />

                <span className="file-picker-button">
                  Choose video
                </span>

                <span className="file-picker-name">
                  {file
                    ? file.name
                    : "No file selected"}
                </span>
              </label>

              <button
                className="button button-primary full-width"
                onClick={uploadVideo}
                disabled={loading}
              >
                {loading
                  ? "Processing video..."
                  : "Upload & Analyze"}
              </button>
            </div>

            <div className="source-divider">
              <span>OR</span>
            </div>

            <div className="source-panel">
              <div className="source-icon">
                ▶
              </div>

              <h3>YouTube URL</h3>

              <p>
                Import a public YouTube video
                directly.
              </p>

              <input
                className="text-input"
                type="url"
                placeholder="https://youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(event) =>
                  setYoutubeUrl(
                    event.target.value
                  )
                }
              />

              <button
                className="button button-secondary full-width"
                onClick={importYoutube}
                disabled={loading}
              >
                {loading
                  ? "Importing..."
                  : "Import from YouTube"}
              </button>
            </div>
          </div>

          {error && (
            <div className="notice notice-error">
              <div className="notice-icon">
                !
              </div>

              <div>
                <strong>
                  Something went wrong
                </strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {successMessage && (
            <div className="notice notice-success">
              <div className="notice-icon">
                ✓
              </div>

              <div>
                <strong>Success</strong>
                <p>{successMessage}</p>
              </div>
            </div>
          )}
        </section>

        {video && (
          <section className="workspace-card">
            <div className="card-heading">
              <div className="step-number">
                02
              </div>

              <div>
                <p className="section-label">
                  ANALYZE
                </p>
                <h2>Video ready</h2>
                <p>
                  Your video passed validation
                  and is ready for clip
                  detection.
                </p>
              </div>
            </div>

            <div className="video-summary">
              <div className="video-file">
                <div className="video-file-icon">
                  ▶
                </div>

                <div>
                  <span>Source video</span>

                  <strong>
                    {video.original_filename ||
                      video.title ||
                      video.stored_filename}
                  </strong>
                </div>
              </div>

              <div className="ready-chip">
                <span>✓</span>
                Ready
              </div>
            </div>

            <div className="metadata-grid">
              <div className="metadata-item">
                <span>Resolution</span>
                <strong>
                  {video.metadata.width} ×{" "}
                  {video.metadata.height}
                </strong>
              </div>

              <div className="metadata-item">
                <span>Duration</span>
                <strong>
                  {formatDuration(
                    video.metadata.duration
                  )}
                </strong>
              </div>

              <div className="metadata-item">
                <span>Frame rate</span>
                <strong>
                  {video.metadata.fps} FPS
                </strong>
              </div>

              <div className="metadata-item">
                <span>Codec</span>
                <strong>
                  {video.metadata.codec.toUpperCase()}
                </strong>
              </div>
            </div>

            <button
              className="button button-primary generate-button"
              onClick={generateClips}
              disabled={segmenting}
            >
              {segmenting ? (
                <>
                  <span className="spinner" />
                  Detecting clips...
                </>
              ) : (
                <>
                  <span>✦</span>
                  Generate Clips
                </>
              )}
            </button>
          </section>
        )}

        {clips.length > 0 && (
          <section className="clips-section">
            <div className="clips-top">
              <div>
                <p className="section-label">
                  03 · EDIT & EXPORT
                </p>

                <h2>Your clips</h2>

                <p>
                  Fine-tune timing, generate
                  vertical versions and export
                  the results.
                </p>
              </div>

              <div className="clips-top-actions">
                <div className="clip-count">
                  {clips.length}{" "}
                  {clips.length === 1
                    ? "clip"
                    : "clips"}
                </div>

                <button
  className="button button-primary export-all"
  onClick={exportAll}
  disabled={exportingAll}
>
  {exportingAll ? (
    <>
      <span className="spinner" />
      Generating & Exporting...
    </>
  ) : (
    <>
      <span>↓</span>
      Export All ({clips.length})
    </>
  )}
</button>
              </div>
            </div>

            <div className="clips-grid">
              {clips.map((clip) => (
                <article
                  className="clip-card"
                  key={clip.clip_id}
                >
                  <div className="clip-card-top">
                    <div>
                      <span className="clip-label">
                        CLIP
                      </span>

                      <h3>
                        Clip {clip.clip_id}
                      </h3>
                    </div>

                    <div className="duration-badge">
                      {clip.duration.toFixed(1)}s
                    </div>
                  </div>

                  {clip.output_filename && (
                    <div className="preview-wrapper">
                      <video
                        className="vertical-preview"
                        controls
                        preload="metadata"
                        src={`http://127.0.0.1:8000/api/preview/${clip.output_filename}`}
                      >
                        Your browser does not
                        support video playback.
                      </video>

                      <div className="preview-badge">
                        9:16
                      </div>
                    </div>
                  )}

                  <div className="timing-section">
                    <div className="timing-heading">
                      <span>Clip timing</span>
                      <span>
                        Adjust before export
                      </span>
                    </div>

                    <div className="clip-times">
                      <label>
                        <span>Start</span>

                        <div className="time-input-wrap">
                          <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={clip.start}
                            onChange={(event) =>
                              updateClipValue(
                                clip.clip_id,
                                "start",
                                Number(
                                  event.target
                                    .value
                                )
                              )
                            }
                          />

                          <span>s</span>
                        </div>
                      </label>

                      <label>
                        <span>End</span>

                        <div className="time-input-wrap">
                          <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={clip.end}
                            onChange={(event) =>
                              updateClipValue(
                                clip.clip_id,
                                "end",
                                Number(
                                  event.target
                                    .value
                                )
                              )
                            }
                          />

                          <span>s</span>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="clip-actions">
                    <button
                      className="button button-ghost"
                      onClick={() =>
                        saveClipTiming(clip)
                      }
                    >
                      Save Timing
                    </button>

                    <button
                      className="button button-primary"
                      onClick={() =>
                        generateVertical(clip)
                      }
                      disabled={
                        clip.generating
                      }
                    >
                      {clip.generating ? (
                        <>
                          <span className="spinner" />
                          Tracking subject...
                        </>
                      ) : clip.output_filename ? (
                        <>
                          <span>↻</span>
                          Regenerate
                        </>
                      ) : (
                        <>
                          <span>✦</span>
                          Generate Vertical
                        </>
                      )}
                    </button>
                  </div>

                  {clip.output_filename && (
                    <div className="completed-area">
                      <div className="ready-badge">
                        <span className="ready-icon">
                          ✓
                        </span>

                        <div>
                          <strong>
                            Vertical clip ready
                          </strong>
                          <span>
                            1080 × 1920 ·
                            Subject tracked
                          </span>
                        </div>
                      </div>

                      <button
                        className="button download-button"
                        onClick={() =>
                          downloadClip(
                            clip.output_filename!
                          )
                        }
                      >
                        <span>↓</span>
                        Download MP4
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </section>
        )}

        <footer className="footer">
          <div className="footer-brand">
            <span>ClipForge</span>
            <span>•</span>
            <span>
              Built for AI Content Lab
            </span>
          </div>

          <p>
            Videos are processed locally.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;