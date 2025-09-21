import asyncio
import platform
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import subprocess
import re

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
    root.geometry("750x800")
    root.configure(bg="#1a1b26")  # Dark blue-gray background

    # Modern color palette (inspired by Catppuccin Mocha)
    colors = {
        "bg": "#1a1b26",         # Dark background
        "frame_bg": "#1e1f30",   # Solid dark blue-gray
        "accent": "#89b4fa",     # Soft blue for buttons
        "accent_hover": "#b4befe",  # Lighter blue for hover
        "text": "#cdd6f4",       # Light text
        "text_secondary": "#a6e3a1",  # Green for secondary text
        "border": "#313244",     # Subtle border
        "highlight": "#f5e0dc",  # Rosewater for highlights
    }

    # Font selection
    font_family = "Inter" if platform.system() == "Windows" else "SF Pro Display"

    # Styling with modern look
    style = ttk.Style()
    style.theme_use("clam")

    # Button style with rounded corners and shadow
    style.configure(
        "Custom.TButton",
        font=(font_family, 12, "bold"),
        padding=(12, 8),
        background=colors["accent"],
        foreground=colors["text"],
        bordercolor=colors["border"],
        borderwidth=0,
        relief="flat",
        anchor="center",
    )
    style.map(
        "Custom.TButton",
        background=[("active", colors["accent_hover"]), ("!disabled", colors["accent"])],
        foreground=[("active", colors["text"]), ("!disabled", colors["text"])],
        shiftrelief=[("active", 2)],
    )

    # Label style
    style.configure(
        "Custom.TLabel",
        background=colors["frame_bg"],
        foreground=colors["text"],
        font=(font_family, 12),
        padding=6,
    )

    # Combobox style
    style.configure(
        "Custom.TCombobox",
        font=(font_family, 11),
        background=colors["frame_bg"],
        foreground=colors["text"],
        fieldbackground=colors["frame_bg"],
        selectbackground=colors["accent"],
        selectforeground=colors["text"],
        bordercolor=colors["border"],
        borderwidth=1,
        arrowsize=12,
    )
    style.map(
        "Custom.TCombobox",
        fieldbackground=[("readonly", colors["frame_bg"])],
        selectbackground=[("readonly", colors["accent"])],
        foreground=[("readonly", colors["text"])],
    )

    # Entry style
    style.configure(
        "Custom.TEntry",
        fieldbackground=colors["frame_bg"],
        foreground=colors["text"],
        bordercolor=colors["border"],
        borderwidth=1,
        font=(font_family, 11),
        padding=8,
    )

    # Listbox style
    style.configure(
        "Custom.TListbox",
        background=colors["frame_bg"],
        foreground=colors["text"],
        font=(font_family, 10),
        selectbackground=colors["accent"],
        selectforeground=colors["text"],
        borderwidth=1,
        relief="flat",
    )

    # Main container
    main_frame = tk.Frame(root, bg=colors["frame_bg"], bd=0)
    main_frame.pack(padx=30, pady=30, fill="both", expand=True)
    main_frame.grid_columnconfigure(0, weight=1)

    # URL Input Frame
    url_frame = tk.Frame(main_frame, bg=colors["frame_bg"], bd=0)
    url_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
    url_frame.grid_columnconfigure(0, weight=1)

    ttk.Label(
        url_frame,
        text="YouTube URL",
        style="Custom.TLabel",
        font=(font_family, 14, "bold"),
        foreground=colors["text_secondary"],
    ).grid(row=0, column=0, sticky="w", pady=(0, 5))
    url_entry = ttk.Entry(url_frame, style="Custom.TEntry")
    url_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    button_frame = tk.Frame(url_frame, bg=colors["frame_bg"])
    button_frame.grid(row=2, column=0, pady=10, sticky="ew")
    button_frame.grid_columnconfigure((0, 1), weight=1)

    fetch_button = ttk.Button(
        button_frame,
        text="Fetch Video",
        style="Custom.TButton",
        command=lambda: threading.Thread(target=fetch_info, daemon=True).start(),
    )
    fetch_button.grid(row=0, column=0, padx=(0, 5), sticky="e")

    download_button = ttk.Button(
        button_frame,
        text="Download",
        style="Custom.TButton",
        command=lambda: threading.Thread(target=start_download, daemon=True).start(),
    )
    download_button.grid(row=0, column=1, padx=(5, 0), sticky="w")

    ttk.Separator(main_frame, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=15, padx=15)

    # Video Info Frame
    info_frame = tk.Frame(main_frame, bg=colors["frame_bg"], bd=0)
    info_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
    info_frame.grid_columnconfigure(0, weight=1)

    thumbnail_label = ttk.Label(info_frame, style="Custom.TLabel")
    thumbnail_label.grid(row=0, column=0, pady=10)

    title_label = ttk.Label(
        info_frame,
        text="",
        style="Custom.TLabel",
        font=(font_family, 14, "bold"),
        wraplength=650,
        justify="center",
        foreground=colors["highlight"],
    )
    title_label.grid(row=1, column=0, pady=5)

    download_options_frame = tk.Frame(info_frame, bg=colors["frame_bg"])
    download_options_frame.grid(row=2, column=0, pady=10)
    download_options_frame.grid_columnconfigure((0, 1), weight=1)

    ttk.Label(
        download_options_frame,
        text="Download Type",
        style="Custom.TLabel",
        font=(font_family, 12),
        foreground=colors["text_secondary"],
    ).grid(row=0, column=0, padx=(0, 10), sticky="w")
    download_type = ttk.Combobox(
        download_options_frame,
        values=["Video", "Audio Only (MP3)"],
        state="readonly",
        width=20,
        style="Custom.TCombobox",
    )
    download_type.set("Video")
    download_type.grid(row=0, column=1, padx=5, sticky="w")

    ttk.Label(
        download_options_frame,
        text="Resolution",
        style="Custom.TLabel",
        font=(font_family, 12),
        foreground=colors["text_secondary"],
    ).grid(row=1, column=0, padx=(0, 10), pady=(10, 0), sticky="w")
    resolution_combo = ttk.Combobox(
        download_options_frame,
        state="readonly",
        width=20,
        style="Custom.TCombobox",
    )
    resolution_combo.grid(row=1, column=1, padx=5, pady=(10, 0), sticky="w")

    progress_label = ttk.Label(
        info_frame,
        text="",
        style="Custom.TLabel",
        font=(font_family, 11),
        wraplength=650,
        foreground=colors["text"],
    )
    progress_label.grid(row=3, column=0, pady=10)

    ttk.Separator(main_frame, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=15, padx=15)

    # Download History Frame
    history_frame = tk.Frame(main_frame, bg=colors["frame_bg"], bd=0)
    history_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=10)
    history_frame.grid_columnconfigure(0, weight=1)

    ttk.Label(
        history_frame,
        text="Download History",
        style="Custom.TLabel",
        font=(font_family, 14, "bold"),
        foreground=colors["text_secondary"],
    ).grid(row=0, column=0, sticky="w", pady=(0, 5))
    history_listbox = tk.Listbox(
        history_frame,
        width=70,
        height=10,
        bg=colors["frame_bg"],
        fg=colors["text"],
        font=(font_family, 10),
        selectbackground=colors["accent"],
        selectforeground=colors["text"],
        bd=1,
        relief="flat",
    )
    history_listbox.grid(row=1, column=0, pady=5, padx=5, sticky="ew")

    # Command functions
    def fetch_info():
        url = url_entry.get().strip()
        if not url:
            root.after(0, lambda: messagebox.showerror("Error", "URL cannot be empty."))
            return

        try:
            yt = YouTube(url)
            root.after(0, lambda: title_label.config(text=yt.title))
            
            response = requests.get(yt.thumbnail_url)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((250, 140), Image.Resampling.LANCZOS)
            thumbnail = ImageTk.PhotoImage(img_data)
            root.after(0, lambda: thumbnail_label.config(image=thumbnail))
            thumbnail_label.image = thumbnail

            if download_type.get() == "Video":
                streams = list_video_streams(yt)
                root.after(0, lambda: resolution_combo.config(values=[s[0] for s in streams]))
                root.after(0, lambda: resolution_combo.set(streams[0][0] if streams else ""))
                resolution_combo.streams = streams
            else:
                root.after(0, lambda: resolution_combo.config(values=[]))
                root.after(0, lambda: resolution_combo.set(""))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch video: {e}"))

    def start_download():
        url = url_entry.get().strip()
        if not url:
            root.after(0, lambda: messagebox.showerror("Error", "URL cannot be empty."))
            return
        
        try:
            yt = YouTube(url)
            if download_type.get() == "Audio Only (MP3)":
                download_audio_only(yt, yt.title, progress_label, history_listbox, root)
            else:
                if not resolution_combo.get():
                    root.after(0, lambda: messagebox.showerror("Error", "Please select a resolution."))
                    return
                selected_stream = resolution_combo.streams[resolution_combo.current()][1]
                download_video_audio(yt, selected_stream, yt.title, progress_label, history_listbox, root)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", f"Download failed: {e}"))

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
                resolution_combo["values"] = []
                resolution_combo.set("")
        else:
            resolution_combo["values"] = []
            resolution_combo.set("")

    download_type.bind("<<ComboboxSelected>>", update_resolution_combo)

    # Window fade-in animation
    def animate_window():
        root.attributes('-alpha', 0.0)
        alpha = 0.0
        while alpha < 1.0:
            alpha += 0.05
            root.attributes('-alpha', alpha)
            root.update()
            root.after(20)

    root.after(100, animate_window)
    root.mainloop()

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(create_ui())
    else:
        create_ui()