import yt_dlp

# Predefined resolutions we want to allow
allowed_res = ["144p", "240p", "360p", "480p", "720p", "1080p", "1080p60"]

url = input("Enter the YouTube URL: ")

# Extract video info without downloading
ydl_opts = {"quiet": True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info_dict = ydl.extract_info(url, download=False)
    formats = info_dict.get("formats", [])

# Filter only allowed resolutions
filtered_formats = []
for f in formats:
    if f.get("format_note") in allowed_res and f.get("ext") == "mp4":
        filtered_formats.append(f)

# Remove duplicates (same resolution appearing multiple times)
unique_formats = {f["format_note"]: f for f in filtered_formats}
filtered_formats = list(unique_formats.values())

# Display available choices
print("\nAvailable Qualities:")
for idx, f in enumerate(filtered_formats, 1):
    print(f"{idx}. {f['format_note']} - {f['ext']} - {round(f['filesize'] / (1024*1024), 2) if f.get('filesize') else 'Unknown'} MB")

# Ask user for choice
choice = int(input("\nEnter choice number: "))
selected_format = filtered_formats[choice - 1]["format_id"]

# Download selected format
download_opts = {
    "format": selected_format,
    "outtmpl": "%(title)s.%(ext)s",
}
with yt_dlp.YoutubeDL(download_opts) as ydl:
    ydl.download([url])

print("\n✅ Download Completed!")
