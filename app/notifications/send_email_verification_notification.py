from app.notifications.base_notification import NotificationSender
from config import config

class EmailVerificationNotification(NotificationSender):
    async def notify(self, to_email: str, token: str):
        verify_url = f"{config['base_url']}auth/verify-email/{token}"

        subject = f"Verify Your Email - {config['app_name']}"
        body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
  <p>Hi,</p>

  <p>Welcome to <strong>{config['app_name']}</strong>! Please verify your email address to activate your account.</p>

  <p>
    <a href="{verify_url}" 
       style="display:inline-block; padding:10px 20px; background-color:#1a73e8; color:#fff; text-decoration:none; border-radius:4px;">
       Verify Email
    </a>
  </p>

  <p>If the above button doesn't work, copy and paste this link into your browser:</p>
  <p style="word-break:break-all; color:#1a73e8;">{verify_url}</p>

  <p>This link will expire in 24 hours. If you did not sign up for {config['app_name']}, please ignore this email.</p>

  <p>Thank you,<br>
  Team {config['app_name']}</p>
</body>
</html>
"""
        await self.send_email(to_email=to_email, subject=subject, body=body)
