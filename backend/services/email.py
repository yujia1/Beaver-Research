import os
import httpx
from pydantic import EmailStr
import logging

logger = logging.getLogger(__name__)

# Brevo API Configuration
BREVO_API_KEY = os.getenv("BREVO_API_KEY", os.getenv("MAIL_PASSWORD"))  # Use MAIL_PASSWORD as fallback
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

async def send_reset_password_email(email: EmailStr, token: str):
    """
    Send a password reset email using Brevo API.
    Uses noreply@beaver-research.cloud as sender
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <html>
    <head></head>
    <body>
        <p>You requested a password reset for Beaver Research.</p>
        <p>Click the link below to verify your email and set a new password:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Link expires in 15 minutes.</p>
    </body>
    </html>
    """
    
    if not BREVO_API_KEY:
        logger.warning(f"MOCK EMAIL (from noreply@beaver-research.cloud) to {email}: {reset_link}")
        logger.warning("BREVO_API_KEY not configured - email not sent")
        print(f"MOCK EMAIL (from noreply@beaver-research.cloud) to {email}: {reset_link}")
        return
    
    payload = {
        "sender": {
            "name": "Beaver Research",
            "email": "noreply@beaver-research.cloud"
        },
        "to": [
            {
                "email": email,
                "name": email.split('@')[0]
            }
        ],
        "subject": "Reset Your Password - Beaver Research",
        "htmlContent": html_content
    }
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    logger.info(f"Sending password reset email to {email} via Brevo API")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BREVO_API_URL, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Password reset email sent successfully. MessageID: {result.get('messageId')}")
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Brevo API error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email: {str(e)}", exc_info=True)
        raise

async def send_verification_email(email: EmailStr, token: str):
    """
    Send an email verification link using Brevo API.
    Uses verification@beaver-research.cloud as sender
    """
    verify_link = f"{FRONTEND_URL}/verify-email?token={token}"
    
    html_content = f"""
    <html>
    <head></head>
    <body>
        <p>Welcome to Beaver Research!</p>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verify_link}">{verify_link}</a></p>
        <p>Link expires in 24 hours.</p>
    </body>
    </html>
    """
    
    if not BREVO_API_KEY:
        logger.warning(f"MOCK EMAIL (from verification@beaver-research.cloud) to {email}: {verify_link}")
        logger.warning("BREVO_API_KEY not configured - email not sent")
        print(f"MOCK EMAIL (from verification@beaver-research.cloud) to {email}: {verify_link}")
        return
    
    payload = {
        "sender": {
            "name": "Beaver Research",
            "email": "verification@beaver-research.cloud"
        },
        "to": [
            {
                "email": email,
                "name": email.split('@')[0]
            }
        ],
        "subject": "Verify Your Email - Beaver Research",
        "htmlContent": html_content
    }
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    logger.info(f"Sending verification email to {email} via Brevo API")
    logger.info(f"API URL: {BREVO_API_URL}")
    logger.info(f"From: verification@beaver-research.cloud")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BREVO_API_URL, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Verification email sent successfully. MessageID: {result.get('messageId')}")
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Brevo API error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send verification email: {str(e)}", exc_info=True)
        raise
