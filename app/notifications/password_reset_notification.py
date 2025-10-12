from app.notifications.base_notification import NotificationSender
from config import config

class PasswordResetNotification(NotificationSender):
    async def notify(self, to_email: str, token: str, expiry_minutes: int = 15):
        reset_url = f"{config['frontend_url']}auth/reset-password?token={token}"

        subject = f"Reset Your Password - {config['app_name']}"
        body = await self.render_template("password_reset.html", {
            "reset_url": reset_url,
            "app_name": config['app_name'],
            "expiry_minutes": expiry_minutes
        })

        await self.send_email(to_email=to_email, subject=subject, body=body)