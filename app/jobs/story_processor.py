# jobs/audio_download_job.py
import os
from yt_dlp import YoutubeDL
from app.services import AudioStoriesService
from config import config
from app.notifications import AudioStoryNotification

os.environ["PATH"] += os.pathsep + config["ffmpeg_path"]

async def download_audio_and_get_info(channel_id: str, file_path: str, file_name: str, user_email: str):
    url = "https://www.youtube.com/watch?v=" + file_path
    save_dir = config["file_download_dir"]
    save_full_path = os.path.join(save_dir, file_name)

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': save_full_path,
        'ffmpeg_location': config["ffmpeg_path"],
        'postprocessors': [],
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        meta_info = {
            "filename": file_name,
            "title": info.get("title"),
            "description": info.get("description"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "channel_url": info.get("channel_url"),
            "webpage_url": info.get("webpage_url"),
            "youtube_id": info.get("id"),
            "thumbnail": info.get("thumbnail")
        }

        # Update story in MongoDB
        audio_stories_service = AudioStoriesService()
        await audio_stories_service.mark_ready(channel_id=channel_id, file_path=file_path, meta_info=meta_info)

        # Send Email Notification
        audio_notification = AudioStoryNotification()
        await audio_notification.notify(
            user_email,
            {
                "title": meta_info["title"],
                "duration": meta_info["duration"],
                "uploader": meta_info["uploader"],
                "filename": file_name,
                "url": url
            }
        )

    except Exception as e:
        raise Exception(f"Download or processing failed: {str(e)}")