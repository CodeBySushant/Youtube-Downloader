# Install pytubefix if not already installed
# !pip install pytubefix

from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import subprocess
import re

def sanitize_filename(name):
    """Replace invalid Windows filename characters with underscore."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def download_highest_quality_video_audio(yt):
    """Download highest quality video and audio, then merge using ffmpeg."""
    print(f"\nDownloading highest quality video and audio for: {yt.title}")

    # Get highest video-only stream
    video_stream = yt.streams.filter(only_video=True, file_extension='mp4').order_by('resolution').desc().first()
    # Get highest audio-only stream
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

    # Download video
    video_file = video_stream.download(filename="temp_video.mp4")
    # Download audio
    audio_file = audio_stream.download(filename="temp_audio.mp3")

    # Sanitize output filename
    output_file = sanitize_filename(yt.title) + ".mp4"
    video_file_escaped = f'"{video_file}"'
    audio_file_escaped = f'"{audio_file}"'
    output_file_escaped = f'"{output_file}"'

    print("\nMerging video and audio with ffmpeg...")
    try:
        subprocess.run(
            f'ffmpeg -y -i {video_file_escaped} -i {audio_file_escaped} -c:v copy -c:a aac {output_file_escaped}',
            shell=True,
            check=True
        )
        print(f"✅ Download complete: {output_file}")
    except Exception as e:
        print(f"❌ Error during merging: {e}")

    # Clean up temporary files
    os.remove(video_file)
    os.remove(audio_file)

def main():
    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("❌ URL cannot be empty.")
        return

    try:
        yt = YouTube(url, on_progress_callback=on_progress)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    print(f"\nTitle: {yt.title}")
    print("Downloading **highest quality** video and audio...")
    download_highest_quality_video_audio(yt)

if __name__ == "__main__":
    main()
