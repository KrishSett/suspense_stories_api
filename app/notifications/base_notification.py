# base_notification.py
import smtplib
from email.message import EmailMessage
from abc import ABC, abstractmethod
from config import config

class NotificationSender(ABC):
    def __init__(self):
        self.mail_host = config["mail_host"]
        self.mail_port = config["mail_port"]
        self.mail_user = config["mail_username"]
        self.mail_pass = config["mail_password"]
        self.mail_from = config["mail_from"]

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.mail_from
            msg["To"] = to_email
            msg.add_alternative(body, subtype='html')

            with smtplib.SMTP(self.mail_host, self.mail_port) as smtp:
                smtp.login(self.mail_user, self.mail_pass)
                smtp.send_message(msg)

            return True
        except Exception as e:
            return False

    @abstractmethod
    async def notify(self, **kwargs):
        pass
