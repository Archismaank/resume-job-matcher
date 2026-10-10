# app/email/mailer.py
"""
Email sending utility using Python's built-in smtplib.
Works with Gmail (requires App Password) or any SMTP server.

To enable:
  1. Enable 2FA on your Google account
  2. Generate an App Password at https://myaccount.google.com/apppasswords
  3. Set SMTP_USER and SMTP_PASSWORD in your .env file
  4. Set EMAIL_VERIFICATION_ENABLED=True in .env
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _build_verification_email(to_email: str, to_name: str, verify_url: str) -> MIMEMultipart:
    """Builds the HTML + plain-text verification email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your Resume Job Matcher account"
    msg["From"] = f"{settings.email_from_name} <{settings.smtp_user}>"
    msg["To"] = to_email

    plain = f"""Hi {to_name},

Thanks for signing up for Resume Job Matcher!

Please verify your email address by visiting the link below:
{verify_url}

This link expires in 24 hours.

If you didn't create an account, you can safely ignore this email.

— The Resume Job Matcher Team
"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ margin:0; padding:0; background:#080705; font-family:'DM Sans',Arial,sans-serif; }}
    .wrapper {{ max-width:560px; margin:40px auto; background:#0f0e0a;
      border:1px solid rgba(201,168,76,0.15); border-radius:20px; overflow:hidden; }}
    .header {{ background:linear-gradient(135deg,#1a1608,#0f0e0a);
      padding:36px 40px 24px; text-align:center;
      border-bottom:1px solid rgba(201,168,76,0.10); }}
    .header .icon {{ font-size:24px; letter-spacing:6px; color:#c9a84c; margin-bottom:12px; }}
    .header h1 {{ margin:0; font-size:22px; font-weight:700; color:#e2c97e;
      font-family:Georgia,serif; }}
    .body {{ padding:32px 40px; }}
    .body p {{ color:#8a8070; font-size:15px; line-height:1.7; margin:0 0 16px 0; }}
    .body .name {{ color:#e2c97e; font-weight:600; }}
    .cta {{ text-align:center; margin:28px 0; }}
    .cta a {{ display:inline-block; padding:14px 36px;
      background:linear-gradient(135deg,#c9a84c,#e8d080);
      color:#080705; font-weight:700; font-size:15px; border-radius:12px;
      text-decoration:none; letter-spacing:0.3px; }}
    .link-fallback {{ background:rgba(201,168,76,0.06);
      border:1px solid rgba(201,168,76,0.15); border-radius:10px;
      padding:12px 16px; margin-top:16px; }}
    .link-fallback p {{ font-size:12px; color:#5a5040; margin:0 0 6px 0; }}
    .link-fallback code {{ color:#c9a84c; font-size:11px; word-break:break-all; }}
    .footer {{ padding:20px 40px; text-align:center;
      border-top:1px solid rgba(201,168,76,0.08); }}
    .footer p {{ color:#3a3020; font-size:12px; margin:0; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="icon">✦ ✦ ✦</div>
      <h1>Verify your email address</h1>
    </div>
    <div class="body">
      <p>Hi <span class="name">{to_name}</span>,</p>
      <p>Thanks for signing up for <b style="color:#c9a84c;">Resume Job Matcher</b>!
         Click the button below to verify your email and activate your account.</p>
      <div class="cta">
        <a href="{verify_url}">Verify My Email →</a>
      </div>
      <div class="link-fallback">
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <code>{verify_url}</code>
      </div>
      <p style="margin-top:24px; font-size:13px; color:#4a4030;">
        This link expires in <b>24 hours</b>. If you didn't create an account,
        you can safely ignore this email.
      </p>
    </div>
    <div class="footer">
      <p>© Resume Job Matcher · Built with FastAPI, Streamlit & OpenAI</p>
    </div>
  </div>
</body>
</html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_verification_email(to_email: str, to_name: str, token: str) -> bool:
    """
    Sends a verification email to the user.
    Returns True on success, False on failure.
    The app still works if email fails — verification is optional per config.
    """
    if not settings.email_verification_enabled:
        logger.info("Email verification disabled — skipping send.")
        return True

    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not configured — skipping email send.")
        return False

    verify_url = f"{settings.app_base_url}/?verify_token={token}"
    msg = _build_verification_email(to_email, to_name, verify_url)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        logger.info(f"Verification email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {to_email}: {e}")
        return False


def _build_password_reset_email(to_email: str, to_name: str, reset_url: str) -> MIMEMultipart:
    """Builds the HTML + plain-text password reset email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your Resume Job Matcher password"
    msg["From"] = f"{settings.email_from_name} <{settings.smtp_user}>"
    msg["To"] = to_email

    plain = f"""Hi {to_name},

We received a request to reset your password for Resume Job Matcher.

Please click the link below to set a new password:
{reset_url}

This link expires in 1 hour.

If you didn't request a password reset, you can safely ignore this email.

— The Resume Job Matcher Team
"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ margin:0; padding:0; background:#080705; font-family:'DM Sans',Arial,sans-serif; }}
    .wrapper {{ max-width:560px; margin:40px auto; background:#0f0e0a;
      border:1px solid rgba(201,168,76,0.15); border-radius:20px; overflow:hidden; }}
    .header {{ background:linear-gradient(135deg,#1a1608,#0f0e0a);
      padding:36px 40px 24px; text-align:center;
      border-bottom:1px solid rgba(201,168,76,0.10); }}
    .header .icon {{ font-size:24px; letter-spacing:6px; color:#c9a84c; margin-bottom:12px; }}
    .header h1 {{ margin:0; font-size:22px; font-weight:700; color:#e2c97e;
      font-family:Georgia,serif; }}
    .body {{ padding:32px 40px; }}
    .body p {{ color:#8a8070; font-size:15px; line-height:1.7; margin:0 0 16px 0; }}
    .body .name {{ color:#e2c97e; font-weight:600; }}
    .cta {{ text-align:center; margin:28px 0; }}
    .cta a {{ display:inline-block; padding:14px 36px;
      background:linear-gradient(135deg,#c9a84c,#e8d080);
      color:#080705; font-weight:700; font-size:15px; border-radius:12px;
      text-decoration:none; letter-spacing:0.3px; }}
    .link-fallback {{ background:rgba(201,168,76,0.06);
      border:1px solid rgba(201,168,76,0.15); border-radius:10px;
      padding:12px 16px; margin-top:16px; }}
    .link-fallback p {{ font-size:12px; color:#5a5040; margin:0 0 6px 0; }}
    .link-fallback code {{ color:#c9a84c; font-size:11px; word-break:break-all; }}
    .footer {{ padding:20px 40px; text-align:center;
      border-top:1px solid rgba(201,168,76,0.08); }}
    .footer p {{ color:#3a3020; font-size:12px; margin:0; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="icon">✦ ✦ ✦</div>
      <h1>Reset your password</h1>
    </div>
    <div class="body">
      <p>Hi <span class="name">{to_name}</span>,</p>
      <p>We received a request to reset your password for <b style="color:#c9a84c;">Resume Job Matcher</b>.
         Click the button below to choose a new password.</p>
      <div class="cta">
        <a href="{reset_url}">Reset Password →</a>
      </div>
      <div class="link-fallback">
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <code>{reset_url}</code>
      </div>
      <p style="margin-top:24px; font-size:13px; color:#4a4030;">
        This link expires in <b>1 hour</b>. If you didn't request a password reset,
        you can safely ignore this email.
      </p>
    </div>
    <div class="footer">
      <p>© Resume Job Matcher · Built with FastAPI, Streamlit & OpenAI</p>
    </div>
  </div>
</body>
</html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_password_reset_email(to_email: str, to_name: str, token: str) -> bool:
    """
    Sends a password reset email to the user.
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not configured — skipping email send.")
        return False

    reset_url = f"{settings.app_base_url}/?reset_token={token}"
    msg = _build_password_reset_email(to_email, to_name, reset_url)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        return False
