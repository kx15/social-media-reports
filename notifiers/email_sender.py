"""Email notifier: send the monthly report via SMTP."""
from __future__ import annotations

import mimetypes
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import config
from utils.helpers import get_logger

logger = get_logger(__name__)


def send(subject: str, body: str, attachments: list[str]) -> None:
    """Send an email with the given *attachments* (file paths) to all configured recipients."""
    if not config.EMAIL_USER or not config.EMAIL_PASSWORD:
        logger.warning("SMTP credentials not configured – skipping email notification.")
        return

    if not config.EMAIL_RECIPIENTS:
        logger.warning("No EMAIL_RECIPIENTS configured – skipping email notification.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_USER
    msg["To"] = ", ".join(config.EMAIL_RECIPIENTS)
    msg.set_content(body)

    for path in attachments:
        if not os.path.exists(path):
            logger.warning("Attachment not found: %s", path)
            continue
        mime_type, _ = mimetypes.guess_type(path)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        with open(path, "rb") as fh:
            msg.add_attachment(
                fh.read(),
                maintype=maintype,
                subtype=subtype,
                filename=Path(path).name,
            )

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            smtp.send_message(msg)
        logger.info("Email sent to: %s", config.EMAIL_RECIPIENTS)
    except smtplib.SMTPException as exc:
        logger.error("Failed to send email: %s", exc)
        raise
