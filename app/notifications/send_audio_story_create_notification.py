from app.notifications.base_notification import NotificationSender
from config import config

class AudioStoryNotification(NotificationSender):
    async def notify(self, to_email: str, meta: dict):
        subject = f"Your audio story is ready: {meta.get('title', 'Untitled')}"
        body = f"""
Hi,

Your YouTube audio has been successfully processed and is ready to use.

Title: {meta.get('title')}
Duration: {meta.get('duration')} seconds
Uploader: {meta.get('uploader')}
File Name: {meta.get('filename')}
Video Url: {meta.get('url')}

Thank you,
Team {config["app_name"]}
"""
        await self.send_email(to_email=to_email, subject=subject, body=body)
