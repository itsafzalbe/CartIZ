from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


def get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token)
    }


@shared_task
def send_verification_email(email, code):
    subject = 'Email Verification Code'
    message = f"""
Hello,

Your verification code is: {code}

This code will expire in 3 minutes.

If you didn't request this code, please ignore this email.
"""

    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]               
    send_mail(
        subject = subject,
        message = message,
        from_email = from_email,
        recipient_list =  recipient_list,
        fail_silently=False,
    )



def verify_google_token(token: str) -> dict:
    try: 
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID,)
    except Exception as exc:
        raise ValueError(f"Invalid Google token {exc}") from exc
    if not id_info.get('email_verified'):
        raise ValueError("Google account email is not verified")
    
    return {
        'sub':            id_info['sub'],
        'email':          id_info['email'],
        'name':           id_info.get('name', ''),
        'picture':        id_info.get('picture', ''),
        'email_verified': id_info.get('email_verified', False),
        'given_name':     id_info.get('given_name', ''),
        'family_name':    id_info.get('family_name', ''),
    }


@shared_task
def send_password_reset_email(email: str, reset_url: str) -> None:
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #00272b;">Reset your password</h2>
        <p style="color: #4a6163;">Click the button below to reset your CartIZ password. This link expires in <strong>24 hours</strong>.</p>
        <a href="{reset_url}"
           style="display:inline-block; padding: 12px 28px; background: #e0ff4f;
                  color: #00272b; font-weight: 700; text-decoration: none;
                  border-radius: 8px; margin: 16px 0;">
            Reset password
        </a>
        <p style="color: #7a9396; font-size: 13px;">
            Or copy this link into your browser:<br>
            <a href="{reset_url}" style="color: #00272b;">{reset_url}</a>
        </p>
        <hr style="border: none; border-top: 1px solid #d4d8c8; margin: 24px 0;">
        <p style="color: #7a9396; font-size: 12px;">
            If you didn't request a password reset, you can safely ignore this email.
        </p>
    </div>
    """

    send_mail(
        subject="Reset your CartIZ password",
        message=f"Reset your password here: {reset_url}\n\nThis link expires in 24 hours.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


