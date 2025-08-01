from app.notifications.base_notification import NotificationSender
from config import config

class EmailVerificationNotification(NotificationSender):
    async def notify(self, to_email: str, token: str):
        verify_url = f"{config['base_url']}auth/verify-email/{token}"

        subject = f"Verify Your Email - {config['app_name']}"
        body = f"""
Hi,

Welcome to {config['app_name']}! Please verify your email address to activate your account.

Click the link below to verify your email:
{verify_url}

If the above link doesn't work, copy and paste it into your browser.

This link will expire in 24 hours. If you did not sign up for {config['app_name']}, please ignore this email.

Thank you,
Team {config['app_name']}
"""
        await self.send_email(to_email=to_email, subject=subject, body=body)
