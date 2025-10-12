from app.notifications.base_notification import NotificationSender
from config import config

class EmailVerificationNotification(NotificationSender):
    async def notify(self, to_email: str, token: str):
        verify_url = f"{config['frontend_url']}auth/verify-email/{token}"

        subject = f"Verify Your Email - {config['app_name']}"
        body = await self.render_template("email_verification.html", {
            "verify_url": verify_url,
            "app_name": config['app_name']
        })
        await self.send_email(to_email=to_email, subject=subject, body=body)
