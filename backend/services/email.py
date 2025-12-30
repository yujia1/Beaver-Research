from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import os
from pathlib import Path

# Configure FastMail
# In a real setup, these would be loaded from env vars
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "apikey"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@beaverresearch.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.sendgrid.net"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

async def send_reset_password_email(email: EmailStr, token: str):
    """
    Send a password reset email to the user.
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    
    html = f"""
    <p>You requested a password reset for Beaver Research.</p>
    <p>Click the link below to verify your email and set a new password:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>If you did not request this, please ignore this email.</p>
    <p>Link expires in 15 minutes.</p>
    """

    message = MessageSchema(
        subject="Reset Your Password - Beaver Research",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    if not conf.MAIL_PASSWORD:
        print(f"MOCK EMAIL to {email}: {reset_link}")
        return

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_verification_email(email: EmailStr, token: str):
    """
    Send an email verification link.
    """
    verify_link = f"{FRONTEND_URL}/verify-email?token={token}"
    
    html = f"""
    <p>Welcome to Beaver Research!</p>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{verify_link}">{verify_link}</a></p>
    <p>Link expires in 24 hours.</p>
    """

    message = MessageSchema(
        subject="Verify Your Email - Beaver Research",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    
    if not conf.MAIL_PASSWORD:
        print(f"MOCK EMAIL to {email}: {verify_link}")
        return

    fm = FastMail(conf)
    await fm.send_message(message)
