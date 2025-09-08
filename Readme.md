# YouTube Downloader (Video & Audio)

A Python script to download YouTube videos and audio. It allows downloading:

- Video with selectable resolution (merging video-only and audio-only streams if needed)
- Audio only (MP3)

---

## Features

- List all available video streams with resolution, FPS, and type (progressive or video-only)
- Download video+audio directly if available
- Merge video-only and highest quality audio streams using **ffmpeg**
- Download audio-only as MP3
- Sanitize file names to avoid invalid characters

---

## Requirements

- Python 3.7+
- `pytubefix` library
- `ffmpeg` installed and added to system PATH

Install `pytubefix` using pip:

```bash
pip install pytubefix
