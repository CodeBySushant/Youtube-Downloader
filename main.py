import yt_dlp

# Ask for video URL
url = input("Enter The URL of Video: ")

# First get available formats
ydl_opts = {}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info_dict = ydl.extract_info(url, download=False)  # Fetch info only
    formats = info_dict.get('formats', [])

    print("\nAvailable Qualities:\n")
    format_list = []
    for i, f in enumerate(formats):
        # Filter only formats with resolution
        if f.get("height"):
            print(f"{i}. {f['format_id']} - {f['ext']} - {f['height']}p - {f.get('fps','')}fps - {f.get('filesize', 'N/A')}")
            format_list.append(f)

    choice = int(input("\nEnter the number of the quality you want to download: "))
    selected_format = format_list[choice]['format_id']

# Now download with selected quality
download_opts = {
    'format': selected_format,
    'outtmpl': '%(title)s.%(ext)s',  # Save as video title
}

with yt_dlp.YoutubeDL(download_opts) as ydl:
    result = ydl.download([url])
    print("\n✅ Video downloaded successfully!")
