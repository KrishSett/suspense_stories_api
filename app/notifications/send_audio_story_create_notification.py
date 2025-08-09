from app.notifications.base_notification import NotificationSender
from config import config


class AudioStoryNotification(NotificationSender):
    async def notify(self, to_email: str, meta: dict):
        subject = f"Your Audio Story Is Ready: {meta.get('title', 'Untitled')}"

        body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
  <p>Hi,</p>

  <p>Your YouTube audio has been successfully processed and is ready to use.</p>

  <div style="margin: 20px 0; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9; align-items: center;">
      <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr>
          <td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #ccc;">Title</td>
          <td style="padding: 6px; border-bottom: 1px solid #ccc;">{meta.get('title')}</td>
        </tr>
        <tr>
          <td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #ccc;">Duration</td>
          <td style="padding: 6px; border-bottom: 1px solid #ccc;">{meta.get('duration')} seconds</td>
        </tr>
        <tr>
          <td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #ccc;">Uploader</td>
          <td style="padding: 6px; border-bottom: 1px solid #ccc;">{meta.get('uploader')}</td>
        </tr>
        <tr>
          <td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #ccc;">File Name</td>
          <td style="padding: 6px; border-bottom: 1px solid #ccc;">{meta.get('filename')}</td>
        </tr>
        <tr>
          <td style="padding: 6px; font-weight: bold;">Video URL</td>
          <td style="padding: 6px;">
            <a href="{meta.get('url')}" style="color: #1a73e8; text-decoration: none;">Watch Video</a>
          </td>
        </tr>
      </table>
  </div>

  <p>Thank you,<br>
  Team {config["app_name"]}</p>
</body>
</html>
"""

        await self.send_email(
            to_email=to_email,
            subject=subject,
            body=body  # assuming send_email detects HTML or sends as HTML
        )
