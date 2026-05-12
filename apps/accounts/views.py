"""
views.py — Authentication & account management
===============================================
All views follow a consistent response envelope:

  Success 2xx
  {
      "status":  "success",
      "message": "...",
      "data":    { ... }   ← omitted when there is nothing to return
  }

  Error 4xx
  {
      "status": "error",
      "errors": { field: [msg, ...], non_field_errors: [...] }
  }
"""


import os
import urllib.parse

from django.shortcuts import redirect
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import *
from .serializers import *


# ─────────────────────────────────────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────────────────────────────────────

def success(message: str, data: dict = None, http_status = status.HTTP_200_OK) -> Response:
    body = {"status": "success", "message": message}
    if data is not None:
        body["data"] = data
    return Response(body, status=http_status)

def created(message: str, data: dict=None) -> Response:
    return success(message, data, http_status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# Custom throttles
# ─────────────────────────────────────────────────────────────────────────────



class AuthRateThrottle(AnonRateThrottle):
    """10 requests / hour for sensitive auth endpoints."""
    scope = "auth"
    rate = "10/hour"

class OTPRateThrottle(AnonRateThrottle):
    """5 OTP requests / hour per IP."""
    scope = "otp"
    rate = "5/hour"

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Submit email => tested 
# ─────────────────────────────────────────────────────────────────────────────
class RegisterEmailView(APIView):
    """
    POST /auth/register/
    Body: { "email": "user@example.com"}
    
    Sends a 5-digit OTP to the provided address
    """

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success(
            "A verification code has been sent to your email address",
            data={"email": user.email},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Verify OTP => tested
# ─────────────────────────────────────────────────────────────────────────────
class VerifyEmailView(APIView):
    """
    POST /auth/verify-email/
    Body: { "email": "user@example.com", "code": "12345" }
    
    On success advances auth_status to REGISTERED and returns the user_id
    the client needs for the complete-profile step.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success(
            "Email verified. Please complete your profile.",
            data = {
                "user_id":     str(user.pk),
                "auth_status": user.auth_status,
            },
        )

# ─────────────────────────────────────────────────────────────────────────────
# Resend OTP => tested
# ─────────────────────────────────────────────────────────────────────────────

class ResendOTPView(APIView):
    """
    POST /auth/resend-otp/
    Body: { "email": "user@example.com" }

    60-second cooldown enforced. Returns seconds_remaining so the frontend
    can display a countdown timer. 
    """

    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(
            "A new verification code has been sent to your email address.",
            data = {"resend_after_seconds": serializer.seconds_until_next},
        )
    

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Complete profile => tested
# ─────────────────────────────────────────────────────────────────────────────

class CompleteProfileView(APIView):
    """
    PATCH /auth/complete-profile/<user_id>/
    Body: { "username", "first_name", "last_name", "password", "password_confirm", ... }
    
    Finalises registration (auth_status → DONE) and immediately issues
    JWT tokens so the user lands on the dashboard without a second login.
    """

    permission_classes = [AllowAny]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id, auth_status="REGISTERED")
        except User.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "User not found or profile setup already completed."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CompleteProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return success(
            "Account created successfully. Welcome!",
            data = {
                "auth_status": user.auth_status,
                "refresh":     str(refresh),
                "access":      str(refresh.access_token),
            }, http_status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Login => tested
# ─────────────────────────────────────────────────────────────────────────────
class LoginView(APIView):
    """
    POST /auth/login/
    Body: { "email": "user@example.com", "password": "SecretPassword123!" }
    Return access + refresh JWT tokens. Also captures the client IP for audit purpose.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = serializer.get_tokens()
        user   = serializer.validated_data["_user"]

        # persist login IP
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
        user.last_login_ip = ip
        user.save(update_fields=["last_login_ip"])

        return success(
            "Logged in successfully.",
            data={
                **tokens,
                "user": {
                    "id":           str(user.pk), 
                    "email":        user.email,
                    "username":     user.username,
                    "first_name":   user.first_name,
                    "last_name":    user.last_name,
                    "auth_status":  user.auth_status,
                    "is_seller":    user.is_seller,
                    "avatar_url":   user.get_avatar_url(),
                },
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# Logout => tested
# ─────────────────────────────────────────────────────────────────────────────
class LogoutView(APIView):
    """
    POST /auth/logout/
    Body: { "refresh": "<refresh_token>" }
    
    Blacklist the refresh token. The short-lived access token will expire
    on its own; frontends should discard it immediately
    """

    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = UserLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Logged out successfully.")


# ─────────────────────────────────────────────────────────────────────────────
# Token refresh => tested
# ─────────────────────────────────────────────────────────────────────────────

class TokenRefreshView(APIView):
    """
    POST /auth/token/refresh/
    Body: { "refresh": <refresh_token> }
    
    Returns a new access token (and rotated refresh if configured).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success("Token refreshed.", data=serializer.get_tokens())


# ─────────────────────────────────────────────────────────────────────────────
# Password — change => tested
# ─────────────────────────────────────────────────────────────────────────────
class PasswordChangeView(APIView):
    """
    POST /auth/password/change/
    Body: { "old_password", "new_password", "new_password_confirm" }
    Requires: Bearer token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Password changed successfully.")


# ─────────────────────────────────────────────────────────────────────────────
# Password — reset request => not tested
# ─────────────────────────────────────────────────────────────────────────────
class PasswordResetRequestView(APIView):
    """
    POST /auth/password/reset/
    Body: { "email": "user@example.com" }
    
    Always 200 - the client cannot tell whether the address exists.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(
            "If that email address is registered you will receive a reset link shortly."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Password — reset confirm => not tested
# ─────────────────────────────────────────────────────────────────────────────

class PasswordResetConfirmView(APIView):
    """
    POST /auth/password/reset/confirm/
    Body: { "uid", "token", "new_password", "new_password_confirm" }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Password reset successfully. You can now log in.")
    


























# # ─────────────────────────────────────────────────────────────────────────────
# # Google OAuth — SPA / mobile
# # ─────────────────────────────────────────────────────────────────────────────

# class GoogleOAuthView(APIView):
#     """
#     POST /auth/google/
#     Body: { "id_token": "<google_id_token>" }

#     For React Native / SPA clients that handle the Google sign-in flow
#     themselves and send the resulting ID token to the backend.
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = GoogleOAuthSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         result = serializer.save()

#         http_status = status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK
#         message     = "Account created via Google." if result["created"] else "Logged in via Google."

#         return success(message, data=result, http_status=http_status)


# # ─────────────────────────────────────────────────────────────────────────────
# # Google OAuth — server-side redirect
# # ─────────────────────────────────────────────────────────────────────────────

# class GoogleOAuthRedirectView(APIView):
#     """
#     GET /auth/google/redirect/

#     Builds the Google consent URL and redirects the browser.
#     Use this for traditional server-rendered or backend-driven OAuth flows.
#     """
#     permission_classes = [AllowAny]

#     def get(self, request):
#         params = urllib.parse.urlencode(
#             {
#                 "client_id":     os.environ.get("GOOGLE_CLIENT_ID", ""),
#                 "redirect_uri":  os.environ.get(
#                     "GOOGLE_REDIRECT_URI",
#                     "http://localhost:8000/auth/google/callback/",
#                 ),
#                 "response_type": "code",
#                 "scope":         "openid email profile",
#                 "access_type":   "offline",
#                 "prompt":        "select_account",
#             }
#         )
#         return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


# class GoogleOAuthCallbackView(APIView):
#     """
#     POST /auth/google/callback/
#     Body: { "code": "<auth_code>", "redirect_uri": "..." }

#     The frontend/backend POSTs here after Google redirects back with a code.
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = GoogleOAuthCallbackSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         result = serializer.save()

#         http_status = status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK
#         message     = "Account created via Google." if result["created"] else "Logged in via Google."

#         return success(message, data=result, http_status=http_status)
    





















# ═════════════════════════════════════════════════════════════════════════════
# USER PROFILE VIEWS => tested
# ═════════════════════════════════════════════════════════════════════════════
class UserProfileView(APIView):
    """
    GET /accounts/me/
    Returns the authenticated user's basic profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return success("Profile retrieved", data=serializer.data)




class UserDetailView(APIView):
    """
    GET /accounts/me/detail/
    Returns the full profile with nested addresses and seller info
    """

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return success("Full profile retrieved.", data=serializer.data)
    


class UserPublicView(APIView):
    """
    GET /accounts/users/<username>/
    Returns limited public info about any user (for review cards, messaging).
    """
    permission_classes = [AllowAny]

    def get(self, request, username: str):
        from django.shortcuts import get_object_or_404
        user = get_object_or_404(User, username=username, is_active=True)
        serializer = UserPublicSerializer(user)
        return success("Public profile retrieved.", data=serializer.data)
    

class UserUpdateView(APIView):
    """
    PATCH /accounts/me/update/
    Updates multiple profile fields (name, phone, dob, username)
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Profile updated.", data=serializer.data)


class UserAvatarUpdateView(APIView):
    """
    PATCH /accounts/me/avatar/
    Accepts multipart/form-data with field 'avatar'.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        serializer = UserAvatarUpdateSerializer(request.user, data=request.data or request.FILES, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success(
            "Profile picture updated.",
            data={"avatar_url": user.get_avatar_url()},
        )


class UserDeleteView(APIView):
    """
    DELETE /accounts/me/delete/
    Body: { "password": "...", "hard_delete": false}
    DEactivates (default) or permanently deletes the account.
    """
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        serializer = UserDeleteSerializer(data=request.data, context={"request": request},)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Account deleted successfully.")



class UserStatsView(APIView):
    """
    GET /accountc/me/stats/
    Returns aggregated statistics for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserStatsSerializer(request.user)
        return success("Activity retrieved.", data=serializer.data)



class UserActivityView(APIView):
    """
    GET /accounts/me/activity/
    Returns the user's recent activity feed.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserActivitySerializer(request.user)
        return success("Acitivity retrieved", data=serializer.data)

# # ═════════════════════════════════════════════════════════════════════════════
# # ADDRESS VIEWS
# # ═════════════════════════════════════════════════════════════════════════════

class UserAddressListCreateView(APIView):
    """
    GET /accounts/me/addresses/         -> list all addresses
    POST /accounts/me/addresses/        -> create a new address
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = request.user.user_address.all()
        serializer = UserAddressListSerializer(addresses, many=True)
        return success("Addresses retrieved.", data={"addresses": serializer.data})
    
    def post(self, request):
        serializer = UserAddressCreateSerializer(data=request.data, context={"request": request}, )
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return created(
            "Address created.",
            data = UserAddressListSerializer(address).data,
        )
    

class UserAddressDetailView(APIView):
    """
    GET /accounts/me/addresses/<id>/      -> retrieve single address
    PATCH /accounts/me/addresses/<id>/    -> update address
    DELETE /accounts/me/addresses/<id>/   -> delete address
    """

    permission_classes = [IsAuthenticated]

    def _get_address(self, request, pk: int) -> UserAddress:
        try:
            return request.user.user_address.get(pk=pk)
        except UserAddress.DoesNotExist:
            return None
    
    def get(self, request, pk: int):
        address = self._get_address(request, pk)
        if not address:
            return Response(
                {"status": "error", "message": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return success("Address retrieved.", data=UserAddressSerializer(address).data)
    
    def patch(self, request, pk: int):
        address = self._get_address(request, pk)
        if not address:
            return Response(
                {"status": "error", "message": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserAddressUpdateSerializer(address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Address updated.", data=UserAddressSerializer(address).data)
    
    def delete(self, request, pk: int):
        serializer = UserAddressDeleteSerializer(
            data={"address_id": pk},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Address deleted.")
 


class SetDefaultAddressView(APIView):
    """
    PATCH /accounts/me/addresses/<id>/set-default/
    Promotes the given address to default, demotes the previous one
    """
    parser_classes = [IsAuthenticated]

    def patch(self, request, pk: int):
        serializer = SetDefaultAddressSerializer(data={"address_id": pk}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return success("Default address updated.", data=UserAddressSerializer(address).data)
