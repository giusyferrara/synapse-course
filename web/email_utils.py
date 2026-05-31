"""SYNAPSE Email utilities — sends transactional emails via Resend HTTPS API."""
import os
import logging
import requests

log = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "SYNAPSE Support")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://synapse-course.com").rstrip("/")
RESEND_ENDPOINT = "https://api.resend.com/emails"


def send_email(to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
    """Send email via Resend. Returns True on success."""
    if not RESEND_API_KEY:
        log.warning("RESEND_API_KEY missing — email not sent")
        return False
    payload = {
        "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    if text_body:
        payload["text"] = text_body
    try:
        r = requests.post(
            RESEND_ENDPOINT,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if r.status_code == 200:
            log.info(f"✅ Email sent to {to_email}: {subject}")
            return True
        log.error(f"❌ Resend {r.status_code}: {r.text[:300]}")
        return False
    except Exception as e:
        log.error(f"❌ Email send failed to {to_email}: {e}")
        return False


def build_reset_email(display_name: str, reset_url: str) -> tuple[str, str]:
    """Return (html, plain_text) bodies for the password-reset email."""
    name = display_name or "there"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f6fa;font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.08);">
    <div style="background:linear-gradient(135deg,#7a5af8 0%,#9b7ff9 100%);padding:32px;color:#fff;text-align:center;">
      <h1 style="margin:0;font-size:26px;">🔐 Password Reset</h1>
    </div>
    <div style="padding:40px 32px;color:#2c2c3e;line-height:1.6;">
      <p style="font-size:16px;">Hi {name},</p>
      <p>We received a request to reset your SYNAPSE password. Click the button below to choose a new one:</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{reset_url}" style="display:inline-block;padding:14px 36px;background:#7a5af8;color:#fff;text-decoration:none;border-radius:10px;font-weight:600;font-size:15px;">Reset my password</a>
      </div>
      <p style="font-size:14px;color:#666;">Or copy and paste this link into your browser:</p>
      <p style="font-size:13px;word-break:break-all;background:#f5f6fa;padding:12px;border-radius:8px;color:#555;">{reset_url}</p>
      <div style="margin-top:32px;padding:16px;background:#fff4e6;border-left:4px solid #ff9f40;border-radius:8px;">
        <p style="margin:0;font-size:14px;color:#8a5a1a;"><strong>⏱️ This link expires in 1 hour.</strong><br>If you didn't request this, you can safely ignore this email.</p>
      </div>
      <p style="margin-top:32px;font-size:13px;color:#888;">— The SYNAPSE team</p>
    </div>
  </div>
</body></html>"""
    plain = (
        f"Hi {name},\n\n"
        f"We received a request to reset your SYNAPSE password.\n"
        f"Open this link to choose a new one:\n\n{reset_url}\n\n"
        f"This link expires in 1 hour. If you didn't request this, ignore this email.\n\n"
        f"— The SYNAPSE team"
    )
    return html, plain
