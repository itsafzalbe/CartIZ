from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


def get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token)
    }



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


