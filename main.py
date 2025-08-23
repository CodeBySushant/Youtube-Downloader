from pytube import YouTube

link = input("Enter The URL of Video: ")
video = YouTube(link)
stream = video.streams.get_highest_resolution()
stream.download()
print("✅ Download complete!")

