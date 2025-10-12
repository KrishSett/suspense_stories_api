import asyncio
from app.notifications.base_notification import NotificationSender
from config import config

class AudioStoryNotification(NotificationSender):
    async def notify(self, to_email: str, meta: dict):
        subject = f"Your Audio Story Is Ready: {meta.get('title', 'Untitled')}"

        body = await self.render_template("audio_story_create.html", {
            "title": meta.get("title"),
            "duration": meta.get("duration"),
            "uploader": meta.get("uploader"),
            "filename": meta.get("filename"),
            "url": meta.get("url"),
            "app_name": config['app_name']
        })

        await self.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )