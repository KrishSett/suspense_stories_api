# base_notification.py
import smtplib
from email.message import EmailMessage
from abc import ABC, abstractmethod
from config import config
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from email.utils import formataddr

class NotificationSender(ABC):
    def __init__(self):
        self.mail_host = config["mail_host"]
        self.mail_port = config["mail_port"]
        self.mail_user = config["mail_username"]
        self.mail_pass = config["mail_password"]
        self.mail_from = config["mail_from"]
        self.mail_from_name = config['mail_from_name']

        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def render_template(self, template_name: str, context: dict) -> str:
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = formataddr((self.mail_from_name, self.mail_from))
            msg["To"] = to_email
            msg.add_alternative(body, subtype='html')

            with smtplib.SMTP(self.mail_host, self.mail_port) as smtp:
                smtp.login(self.mail_user, self.mail_pass)
                smtp.send_message(msg)

            return True
        except ValueError as e:
            return False

    @abstractmethod
    async def notify(self, **kwargs):
        pass
