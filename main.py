from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import subprocess
import re
import uuid

# Folder for all downloads
DOWNLOAD_FOLDER = "Downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(name):
    """Replace invalid Windows filename characters with underscore."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def list_video_streams(yt):
    """List all available video streams with resolution and type."""
    streams = yt.streams.filter(file_extension='mp4').order_by('resolution').desc()
    print("\nAvailable video streams:")
    for i, stream in enumerate(streams, start=1):
        type_info = "Video+Audio" if stream.is_progressive else "Video-only"
        print(f"{i}. Resolution: {stream.resolution or 'N/A'}, FPS: {stream.fps or 'N/A'}, Type: {type_info}")
    return streams

def download_video_audio(yt):
    """Download selected video and highest quality audio, then merge without overwriting."""
    streams = list_video_streams(yt)
    choice = input("\nEnter the number of the resolution to download (or press Enter for highest): ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(streams):
        video_stream = streams[int(choice)-1]
    else:
        video_stream = streams[0]  # highest resolution by default

    unique_id = uuid.uuid4().hex  # Generate unique ID

    if video_stream.is_progressive:
        print(f"\nDownloading video+audio: {video_stream.resolution}")
        video_file = video_stream.download(
            output_path=DOWNLOAD_FOLDER,
            filename=sanitize_filename(yt.title) + f"_{unique_id}.mp4"
        )
        print(f"✅ Download complete: {video_file}")
        return

    print(f"\nDownloading video-only stream: {video_stream.resolution}")
    video_file = video_stream.download(
        output_path=DOWNLOAD_FOLDER,
        filename=f"temp_video_{unique_id}.mp4"
    )
    
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    audio_file = audio_stream.download(
        output_path=DOWNLOAD_FOLDER,
        filename=f"temp_audio_{unique_id}.mp3"
    )

    output_file = os.path.join(
        DOWNLOAD_FOLDER,
        sanitize_filename(yt.title) + f"_{unique_id}.mp4"
    )

    print("\nMerging video and audio with ffmpeg...")
    try:
        subprocess.run(
            f'ffmpeg -y -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac "{output_file}"',
            shell=True,
            check=True
        )
        print(f"✅ Download complete: {output_file}")
    except Exception as e:
        print(f"❌ Error during merging: {e}")

    os.remove(video_file)
    os.remove(audio_file)

def download_audio_only(yt):
    """Download audio only and convert to mp3 without overwriting previous downloads."""
    print(f"\nDownloading audio only: {yt.title}")

    unique_id = uuid.uuid4().hex  # Generate unique ID

    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    temp_audio_filename = f"temp_audio_{unique_id}.mp3"
    out_file = audio_stream.download(
        output_path=DOWNLOAD_FOLDER,
        filename=temp_audio_filename
    )
    
    new_file = os.path.join(
        DOWNLOAD_FOLDER,
        sanitize_filename(yt.title) + f"_{unique_id}.mp3"
    )
    os.rename(out_file, new_file)

    print(f"✅ Audio download complete: {new_file}")

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
    print("\nChoose download option:")
    print("1 - Video (choose resolution, merge audio if needed)")
    print("2 - Audio only (mp3, music)")

    choice = input("Enter choice (1 or 2): ").strip()
    if choice == '1':
        download_video_audio(yt)
    elif choice == '2':
        download_audio_only(yt)
    else:
        print("❌ Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
