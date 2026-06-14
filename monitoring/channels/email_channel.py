"""Email notification channel."""

from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


class EmailChannel:
    """Send alerts via SMTP email."""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.host = smtp_host
        self.port = smtp_port
        self.username = username
        self.password = password

    def send(self, subject: str, body: str, recipients: List[str]) -> bool:
        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = ", ".join(recipients)
            with smtplib.SMTP(self.host, self.port) as s:
                s.starttls()
                s.login(self.username, self.password)
                s.send_message(msg)
            return True
        except Exception as e:
            logger.warning("Email send failed: %s", e)
            return False
