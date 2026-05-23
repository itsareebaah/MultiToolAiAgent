"""Send email via SMTP."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(to: str, subject: str, body: str) -> str:
    to = to.strip()
    subject = subject.strip()
    if not to:
        return "Error: recipient email (to) is required."
    if not subject:
        return "Error: email subject is required."
    if not body.strip():
        return "Error: email body cannot be empty."

    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("EMAIL_FROM", user)

    if not user or not password:
        return (
            "Error: SMTP not configured. Set SMTP_USER, SMTP_PASSWORD, and "
            "EMAIL_FROM in your .env file (see .env.example)."
        )

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(from_addr, [to], msg.as_string())
    except smtplib.SMTPException as exc:
        return f"Failed to send email: {exc}"
    except OSError as exc:
        return f"Failed to connect to SMTP server: {exc}"

    return f"Email sent successfully to {to} with subject: {subject}"
