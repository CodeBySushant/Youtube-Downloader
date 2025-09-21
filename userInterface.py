from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import subprocess
import re
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading

# Folder for all downloads
DOWNLOAD_FOLDER = "Downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(name):
    """Replace invalid Windows filename characters with underscore."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def list_video_streams(yt):
    """List all available video streams with resolution and type."""
    streams = yt.streams.filter(file_extension='mp4').order_by('resolution').desc()
    return [(f"{stream.resolution or 'N/A'} ({stream.fps or 'N/A'} FPS, {'Video+Audio' if stream.is_progressive else 'Video-only'})", stream) for stream in streams]

def download_video_audio(yt, stream, title, progress_label, history_listbox, root):
    """Download selected video and highest quality audio, then merge without overwriting."""
    unique_id = uuid.uuid4().hex
    output_file = os.path.join(DOWNLOAD_FOLDER, f"{sanitize_filename(title)}_{unique_id}.mp4")
    
    def update_progress(stream, chunk, bytes_remaining):
        """Update progress label during download."""
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        root.after(0, lambda: progress_label.config(text=f"Downloading: {percentage:.1f}%"))

    if stream.is_progressive:
        progress_label.config(text=f"Downloading video+audio: {stream.resolution}")
        video_file = stream.download(
            output_path=DOWNLOAD_FOLDER,
            filename=sanitize_filename(title) + f"_{unique_id}.mp4",
            on_progress_callback=update_progress
        )
        root.after(0, lambda: progress_label.config(text=f"✅ Download complete: {os.path.basename(video_file)}"))
        root.after(0, lambda: history_listbox.insert(tk.END, os.path.basename(video_file)))
        return

    progress_label.config(text=f"Downloading video: {stream.resolution}")
    video_file = stream.download(
        output_path=DOWNLOAD_FOLDER,
        filename=f"temp_video_{unique_id}.mp4",
        on_progress_callback=update_progress
    )
    
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    progress_label.config(text="Downloading audio...")
    audio_file = audio_stream.download(
        output_path=DOWNLOAD_FOLDER,
        filename=f"temp_audio_{unique_id}.mp3",
        on_progress_callback=update_progress
    )

    progress_label.config(text="Merging video and audio...")
    try:
        subprocess.run(
            f'ffmpeg -y -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac "{output_file}"',
            shell=True,
            check=True
        )
        root.after(0, lambda: progress_label.config(text=f"✅ Download complete: {os.path.basename(output_file)}"))
        root.after(0, lambda: history_listbox.insert(tk.END, os.path.basename(output_file)))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Failed to merge: {e}"))
    finally:
        try:
            os.remove(video_file)
            os.remove(audio_file)
        except:
            pass

def download_audio_only(yt, title, progress_label, history_listbox, root):
    """Download audio only and convert to mp3 without overwriting previous downloads."""
    unique_id = uuid.uuid4().hex
    temp_audio_filename = f"temp_audio_{unique_id}.mp3"
    new_file = os.path.join(DOWNLOAD_FOLDER, f"{sanitize_filename(title)}_{unique_id}.mp3")

    def update_progress(stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        root.after(0, lambda: progress_label.config(text=f"Downloading audio: {percentage:.1f}%"))

    progress_label.config(text="Downloading audio...")
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    out_file = audio_stream.download(
        output_path=DOWNLOAD_FOLDER,
        filename=temp_audio_filename,
        on_progress_callback=update_progress
    )
    
    os.rename(out_file, new_file)
    root.after(0, lambda: progress_label.config(text=f"✅ Audio download complete: {os.path.basename(new_file)}"))
    root.after(0, lambda: history_listbox.insert(tk.END, os.path.basename(new_file)))

def create_ui():
    root = tk.Tk()
    root.title("YouTube Downloader")
    root.geometry("600x600")
    root.configure(bg="#f0f0f0")

    # Styling
    style = ttk.Style()
    style.configure("TButton", padding=6, font=("Helvetica", 10))
    style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 10))
    style.configure("TCombobox", font=("Helvetica", 10))

    # URL Input
    ttk.Label(root, text="Enter YouTube URL:", font=("Helvetica", 12, "bold")).pack(pady=10)
    url_entry = ttk.Entry(root, width=50)
    url_entry.pack(pady=5)

    # Thumbnail
    thumbnail_label = ttk.Label(root, text="", background="#f0f0f0")
    thumbnail_label.pack(pady=10)

    # Video Title
    title_label = ttk.Label(root, text="", font=("Helvetica", 12, "bold"), wraplength=500, justify="center")
    title_label.pack(pady=5)

    # Download Type
    ttk.Label(root, text="Download Type:", font=("Helvetica", 10, "bold")).pack(pady=5)
    download_type = ttk.Combobox(root, values=["Video", "Audio Only (MP3)"], state="readonly", width=20)
    download_type.set("Video")
    download_type.pack(pady=5)

    # Resolution Selection
    resolution_frame = ttk.Frame(root)
    resolution_frame.pack(pady=5)
    ttk.Label(resolution_frame, text="Resolution:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
    resolution_combo = ttk.Combobox(resolution_frame, state="readonly", width=30)
    resolution_combo.pack(side=tk.LEFT, padx=5)

    # Progress Label
    progress_label = ttk.Label(root, text="", font=("Helvetica", 10), wraplength=500)
    progress_label.pack(pady=10)

    # Download History
    ttk.Label(root, text="Download History:", font=("Helvetica", 10, "bold")).pack(pady=5)
    history_listbox = tk.Listbox(root, width=50, height=8)
    history_listbox.pack(pady=5)

    # Fetch Video Info
    def fetch_info():
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "URL cannot be empty.")
            return

        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            title_label.config(text=yt.title)
            
            # Fetch and display thumbnail
            response = requests.get(yt.thumbnail_url)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((200, 112), Image.Resampling.LANCZOS)
            thumbnail = ImageTk.PhotoImage(img_data)
            thumbnail_label.config(image=thumbnail)
            thumbnail_label.image = thumbnail  # Keep reference

            # Populate resolutions
            if download_type.get() == "Video":
                streams = list_video_streams(yt)
                resolution_combo["values"] = [s[0] for s in streams]
                resolution_combo.set(streams[0][0] if streams else "")
                resolution_combo.streams = streams
            else:
                resolution_combo["values"] = []
                resolution_combo.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch video: {e}")

    # Download Button Action
    def start_download():
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "URL cannot be empty.")
            return

        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            if download_type.get() == "Audio Only (MP3)":
                threading.Thread(target=download_audio_only, args=(yt, yt.title, progress_label, history_listbox, root), daemon=True).start()
            else:
                if not resolution_combo.get():
                    messagebox.showerror("Error", "Please select a resolution.")
                    return
                selected_stream = resolution_combo.streams[resolution_combo.current()][1]
                threading.Thread(target=download_video_audio, args=(yt, selected_stream, yt.title, progress_label, history_listbox, root), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {e}")

    # Buttons
    ttk.Button(root, text="Fetch Video Info", command=fetch_info).pack(pady=5)
    ttk.Button(root, text="Download", command=start_download).pack(pady=5)

    # Update resolution combo when download type changes
    def update_resolution_combo(event):
        url = url_entry.get().strip()
        if url and download_type.get() == "Video":
            try:
                yt = YouTube(url)
                streams = list_video_streams(yt)
                resolution_combo["values"] = [s[0] for s in streams]
                resolution_combo.set(streams[0][0] if streams else "")
                resolution_combo.streams = streams
            except:
                pass
        else:
            resolution_combo["values"] = []
            resolution_combo.set("")

    download_type.bind("<<ComboboxSelected>>", update_resolution_combo)

    root.mainloop()

if __name__ == "__main__":
    create_ui()