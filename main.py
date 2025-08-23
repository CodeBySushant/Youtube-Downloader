import yt_dlp

url = input("Enter The URL of Video: ")

ydl_opts = {
    'format': 'best',
    'outtmpl': '%(title)s.%(ext)s',  # Save as video title
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
