"""Notifications — email (SMTP / Gmail API) + Home Assistant webhook.

Intentionally minimal: send functions + an env-driven dispatcher.
`send_all(title, body, severity)` fans out to every configured channel.

Email priority: SMTP (if ARCHIVIST_SMTP_PASSWORD set) > Gmail API (if OAuth
token has gmail.send scope). SMTP is simpler and doesn't require OAuth consent
for the send scope.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

logger = logging.getLogger("archivist.notifications")

# Channel config (all optional — channel is skipped if its env is unset)
ALERT_EMAIL = os.getenv("ARCHIVIST_ALERT_EMAIL", "").strip()
HA_WEBHOOK_URL = os.getenv("HA_WEBHOOK_URL", "").strip()
HA_WEBHOOK_TOKEN = os.getenv("HA_WEBHOOK_TOKEN", "").strip()

# SMTP config (use Gmail App Password — no OAuth needed)
SMTP_HOST = os.getenv("ARCHIVIST_SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("ARCHIVIST_SMTP_PORT", "587"))
SMTP_USER = os.getenv("ARCHIVIST_SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("ARCHIVIST_SMTP_PASSWORD", "").strip()

# Gmail API send reuses the same OAuth token store as ingest
GOOGLE_ACCOUNTS_DIR = Path(os.getenv(
    "ARCHIVIST_GOOGLE_ACCOUNTS_DIR", "/root/.config/archivist/google-accounts"
))


def _send_email_smtp(subject: str, body: str, to: str) -> bool:
    """Send via SMTP (Gmail App Password). No OAuth needed."""
    sender = SMTP_USER or ALERT_EMAIL
    if not sender or not SMTP_PASSWORD:
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["To"] = to
        msg["From"] = sender
        msg["Subject"] = subject
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(sender, SMTP_PASSWORD)
            server.sendmail(sender, [to], msg.as_string())
        return True
    except Exception:
        logger.exception("SMTP send failed")
        return False


def _send_email_gmail_api(subject: str, body: str, to: str) -> bool:
    """Send via Gmail API using OAuth token with gmail.send scope."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except Exception:
        logger.debug("google libs missing; gmail API disabled")
        return False

    creds = _load_gmail_creds()
    if creds is None:
        return False

    try:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        msg = MIMEText(body, "plain", "utf-8")
        msg["To"] = to
        msg["Subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception:
        logger.exception("gmail API send failed")
        return False


def send_email(subject: str, body: str, to: Optional[str] = None) -> bool:
    """Send email via SMTP (preferred) or Gmail API fallback."""
    recipient = (to or ALERT_EMAIL).strip()
    if not recipient:
        return False
    if SMTP_PASSWORD:
        return _send_email_smtp(subject, body, recipient)
    return _send_email_gmail_api(subject, body, recipient)


def _load_gmail_creds():
    """Pick the first token file that includes gmail.send scope."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except Exception:
        return None
    if not GOOGLE_ACCOUNTS_DIR.is_dir():
        return None
    required_scope = "https://www.googleapis.com/auth/gmail.send"
    for token_path in GOOGLE_ACCOUNTS_DIR.glob("*.json"):
        try:
            data = json.loads(token_path.read_text())
        except Exception:
            continue
        scopes = data.get("scopes") or []
        if required_scope not in scopes:
            continue
        try:
            creds = Credentials.from_authorized_user_info(data, scopes)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json())
            return creds
        except Exception:
            logger.exception("failed to load creds %s", token_path)
    return None


def send_ha_webhook(title: str, body: str, severity: str) -> bool:
    """POST to a Home Assistant webhook URL. HA side decides fan-out."""
    if not HA_WEBHOOK_URL:
        return False
    try:
        import requests
    except Exception:
        return False
    headers = {"Content-Type": "application/json"}
    if HA_WEBHOOK_TOKEN:
        headers["Authorization"] = f"Bearer {HA_WEBHOOK_TOKEN}"
    payload = {"title": title, "message": body, "severity": severity, "source": "archivist"}
    try:
        r = requests.post(HA_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        return r.status_code < 400
    except Exception:
        logger.exception("ha webhook failed")
        return False


BROADCAST_PORT = int(os.getenv("ARCHIVIST_BROADCAST_PORT", "9199"))
BROADCAST_ENABLED = (os.getenv("ARCHIVIST_BROADCAST_ALERTS") or "true").strip().lower() in ("1", "true", "yes", "on")


def send_broadcast(title: str, body: str, severity: str) -> bool:
    """Send a UDP broadcast on the LAN so any listener can pick up critical alerts."""
    if not BROADCAST_ENABLED:
        return False
    try:
        import json
        import socket
        msg = json.dumps({
            "type": "archivist_alert",
            "title": title,
            "message": body,
            "severity": severity,
            "source": "archivist",
            "host": socket.gethostname(),
        }, separators=(",", ":")).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.sendto(msg, ("<broadcast>", BROADCAST_PORT))
            return True
        finally:
            sock.close()
    except Exception:
        logger.debug("broadcast alert failed", exc_info=True)
        return False


def send_all(title: str, body: str, severity: str = "warning") -> dict:
    """Fan out to every configured channel. Returns which channels succeeded."""
    return {
        "email": send_email(f"[archivist:{severity}] {title}", body),
        "ha": send_ha_webhook(title, body, severity),
        "broadcast": send_broadcast(title, body, severity),
    }


def channels_configured() -> dict:
    """For /health diagnostics."""
    return {
        "email": bool(ALERT_EMAIL and (SMTP_PASSWORD or _load_gmail_creds() is not None)),
        "ha": bool(HA_WEBHOOK_URL),
        "broadcast": BROADCAST_ENABLED,
    }
