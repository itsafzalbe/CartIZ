from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
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
def send_verification_email(email: str, code: str) -> None:
    """
    Sends the 5-digit OTP to `email`.
    Uses the branded HTML template at templates/emails/verify_email.html.
    Falls back to plain-text if the template fails.
    """
    subject = "Your CartIZ verification code"

    # Split code into individual digits for the template
    digits = list(str(code))

    # Plain-text fallback
    plain = (
        f"Your CartIZ verification code is: {code}\n\n"
        f"This code will expire in 3 minutes.\n\n"
        f"If you didn't request this code, please ignore this email."
    )

    try:
        html = render_to_string("emails/verify_email.html", {"code": digits})
    except Exception:
        html = None

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=f"CartIZ <{settings.EMAIL_HOST_USER}>",
        to=[email],
    )
    if html:
        msg.attach_alternative(html, "text/html")

    msg.send(fail_silently=False)


@shared_task
def send_password_reset_email(email: str, reset_url: str, first_name: str = "") -> None:
    """
    Sends the password-reset link to `email`.
    Uses the branded HTML template at templates/emails/password_reset.html.
    Falls back to plain-text if the template fails.
    """
    subject = "Reset your CartIZ password"

    display_name = first_name or "there"

    # Plain-text fallback
    plain = (
        f"Hi {display_name},\n\n"
        f"We received a request to reset the password for your CartIZ account.\n\n"
        f"Click the link below to reset your password (expires in 1 hour):\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, you can safely ignore this email."
    )

    try:
        html = render_to_string("emails/password_reset.html", {
            "reset_url": reset_url,
            "email": email,
            "first_name": display_name,
        })
    except Exception:
        html = None

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=f"CartIZ <{settings.EMAIL_HOST_USER}>",
        to=[email],
    )
    if html:
        msg.attach_alternative(html, "text/html")

    msg.send(fail_silently=False)


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
