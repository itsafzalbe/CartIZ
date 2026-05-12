"""
serializers.py — Authentication & account management
=====================================================
Registration flow  (3 steps, tracked via auth_status):
  Step 1  POST /auth/register/              email → OTP sent          (NEW)
  Step 2  POST /auth/verify-email/          OTP  → email confirmed    (NEW → REGISTERED)
  Step 3  PATCH /auth/complete-profile/     profile + password set    (REGISTERED → DONE)
 
OTP resend:
  POST /auth/resend-otp/   allowed once per 60 s; max 5 attempts per session.
 
Session:
  POST /auth/login/
  POST /auth/logout/
  POST /auth/token/refresh/
 
Password:
  POST /auth/password/change/
  POST /auth/password/reset/
  POST /auth/password/reset/confirm/
 
Google OAuth (two flows):
  POST /auth/google/           — SPA / mobile (send ID token directly)
  POST /auth/google/callback/  — server-side (exchange authorization code)
"""



import os
import requests as http_requests
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.db import transaction

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import uuid
from .utils import *

from .models import User, EmailVerification, UserAddress



OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_RESENDS = 5

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────


def _issue_tokens(user: User) -> dict:
    # returns a fresh JWT access + refresh pair for *user*

    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _get_unverified_user(email: str) -> User:
    # returns an univerified user by email or raise a validation error
    try:
        return User.objects.get(email=email.lower().strip(), is_email_verified=False)
    except User.DoesNotExist:
        raise serializers.ValidationError({
            "email": "No pending verification found for this address"
        })

def _send_otp(user: User) -> None:
    code = user.generate_code()
    EmailVerification.objects.create(user=user, code=code)
    send_verification_email(user.email, code)



def _get_own_address(user: User, address_id: int) -> UserAddress:
    """Return a UserAddress that belong to *user* or raise validation error"""
    try:
        return UserAddress.objects.get(pk=address_id, user=user)
    except UserAddress.DoesNotExist:
        raise serializers.ValidationError("Address not found")




#
# 1. ACCOUNTS APP (40 serializers)Authentication & Registration:
#
# UserRegistrationSerializer - Handles new user signup with email, username, and password - Done
# UserLoginSerializer - Authenticates user credentials and returns auth tokens - Done
# UserLogoutSerializer - Invalidates refresh token and logs user out - Done
# EmailVerificationSerializer - Verifies user email address with token - Done
# ResendVerificationEmailSerializer - Resends email verification link - Done
# RefreshTokenSerializer - Generates new access token from refresh token - Done
# PasswordChangeSerializer - Changes password for authenticated users - Done
# PasswordResetRequestSerializer - Sends password reset link to user's email - Done
# PasswordResetConfirmSerializer - Resets password using token from email - Done



# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Submit email  (auth_status stays NEW)
# ─────────────────────────────────────────────────────────────────────────────


class UserRegistrationSerializer(serializers.Serializer):
    """
    Accepts an email address and fires an OTP
    - New email -> create inactive/unverified user, send OTP
    - Partially done -> reset status, resend OTP (lets users retry)
    - Fully registered -> reject with a clear message
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        user = User.objects.filter(email = value).first()
        if user and user.is_email_verified and user.auth_status == "DONE":
            raise serializers.ValidationError("An account with this email already exists. Please login.")
        return value

    def save(self) -> User:
        email = self.validated_data["email"]

        user, created = User.objects.get_or_create(
            email = email, 
            defaults={
                "auth_status": "NEW", 
                "is_active": False,
                "is_email_verified": False,
            },
        )
        
        if not created:
            user.auth_status = "NEW"
            user.is_email_verified = False
            user.is_active = False
            user.save(update_fields=["auth_status", "is_email_verified", "is_active"])

        _send_otp(user)
        return user
    

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Verify OTP  (auth_status: NEW → REGISTERED)
# ─────────────────────────────────────────────────────────────────────────────


class EmailVerificationSerializer(serializers.Serializer):
    """ 
    Verifies the 5 digit OTP
    On success auth_status advances to REGISTERED and the account is activated.
    """


    email = serializers.EmailField()
    code = serializers.CharField(max_length=5, min_length=5)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        code = attrs["code"].strip()
        
        user = _get_unverified_user(email)
        
        verification = EmailVerification.objects.filter(user=user, confirmed=False).order_by("-created_at").first()
        
        if not verification:
            raise serializers.ValidationError(
                {"code": "No active verification code found. Please request a new one."}
            )
        
        if verification.is_expired():
            raise serializers.ValidationError(
                {"code": "This code has expired. Please request a new one."}
            )
        
        if verification.code != code:
            raise serializers.ValidationError(
                {"code": "Incorrect verification code. Please check and try again"}
            )
        
        attrs["_user"] = user
        attrs["_verification"] = verification
        return attrs
    
    def save(self):
        user         = self.validated_data["_user"]
        verification = self.validated_data["_verification"]

        verification.confirmed = True
        verification.save(update_fields=["confirmed"])

        user.is_email_verified = True
        user.auth_status = "REGISTERED"
        user.is_active = True
        user.save(update_fields=["is_email_verified", "auth_status", "is_active"])
        return user





# ─────────────────────────────────────────────────────────────────────────────
# Resend OTP
# ─────────────────────────────────────────────────────────────────────────────


class ResendVerificationEmailSerializer(serializers.Serializer):
    """
    Resends the OTP under these rule:
        * 60-second cooldown between consecutive requests
        * After OTP_MAX_RESENDS unconfirmed codes the user must restart
        registration (prevents brute-force / abuse)
    """

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        value = value.lower().strip()
        self._user = _get_unverified_user(value)

        pending_count = EmailVerification.objects.filter(user=self._user, confirmed = False).count()
        if pending_count >= OTP_MAX_RESENDS:
            raise serializers.ValidationError(
                f"You have requested too many codes."
                f"Please restart registration with your email address"
            )
        
        if not self._user.can_resend_code():
            raise serializers.ValidationError(
                f"Please wait {OTP_RESEND_COOLDOWN_SECONDS} seconds"
                f" before requesting another code"
            )
        return value
    
    def save(self) -> None:
        _send_otp(self._user)

    
    @property
    def seconds_until_next(self) -> int:
        """Helper the view can expose in the response body"""
        last = EmailVerification.objects.filter(user=self._user, confirmed=False).order_by("-created_at").first()
        if not last:
            return 0
        elapsed = (timezone.now() - last.created_at).total_seconds()
        return max(0, int(OTP_RESEND_COOLDOWN_SECONDS - elapsed))
        
 

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Complete profile  (auth_status: REGISTERED → DONE)
# ─────────────────────────────────────────────────────────────────────────────
class CompleteProfileSerializer(serializers.ModelSerializer):
    """
    Collects remaining profile fields + password
    On success issues JWT tokens so the user is immediately logged in
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username", "first_name", "last_name", 
            "phone_number", "date_of_birth", 
            "password", "password_confirm",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This username already taken")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return attrs
    
    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.set_password(password)
        instance.auth_status = "DONE"
        instance.save()
        return instance



# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

class UserLoginSerializer(serializers.Serializer):
    """
    Validates email + password and returns JWT tokens
    Tracks failed attempts and locks the account after 5 failures.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs["email"].lower().strip()
        password = attrs["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # generic message to prevent user enumeration
            raise serializers.ValidationError(
                {"non_failed_errors": "Invalid credentials"}
            )
        
        if user.is_locked:
            from django.utils.timesince import timeuntil

            raise serializers.ValidationError(
                {
                    "non_failed_errors": (
                        "Your account is temporarily locked due to too many failed "
                        f"attempts. Try again in {timeuntil(user.locked_until)}."
                    )
                }
            )
        
        if not user.is_email_verified:
            raise serializers.ValidationError(
                {"email": "Please verify your email address before logging in."}
            )
        if user.auth_status != "DONE":
            raise serializers.ValidationError(
                {"non_failed_errors": "Please complete your account setup first."}
            )

        authenticated = authenticate(username = email, password=password)
        if not authenticated:
            user.increment_failed_login()
            attempts_left = max(0, 5 - user.failed_login_attempts)
            msg = (
                f"Invalid credentials. {attempts_left} attempt(s) remaining."
                if attempts_left > 0
                else "Invalid credentials. Your account has been locked for 30 minutes"
            )
            raise serializers.ValidationError({"non_failed_errors": msg})
        
        user.reset_failed_login()
        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        attrs["_user"] = authenticated
        return attrs
    
    def get_tokens(self) -> dict:
        return _issue_tokens(self.validated_data["_user"])



# ─────────────────────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────────────────────
class UserLogoutSerializer(serializers.Serializer):
    """Blacklist the refresh token to invalidate the session."""

    refresh = serializers.CharField()

    def validate_refresh(self, value: str) -> str:
        try:
            self._token = RefreshToken(value)
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token")
        return value
    
    def save(self) -> None:
        self._token.blacklist()


# ─────────────────────────────────────────────────────────────────────────────
# Token refresh
# ─────────────────────────────────────────────────────────────────────────────
class RefreshTokenSerializer(serializers.Serializer):
    """
    Returns a fresh access token.
    If ROTATE_REFRESH_TOKENS = True a new refresh token is also issued
    and the old one is blacklisted automatically by simplejwt.
    """

    refresh = serializers.CharField()

    def validate_refresh(self, value: str) -> str:
        try:
            self._token = RefreshToken(value)
        except TokenError:
            raise serializers.ValidationError("INvalid or expired refresh token.")
        return value
    
    def get_tokens(self) -> dict:
        return {
            "access":  str(self._token.access_token),
            "refresh": str(self._token),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Password — change (requires authentication)
# ─────────────────────────────────────────────────────────────────────────────

class PasswordChangeSerializer(serializers.Serializer):
    """Changes the password for the currently authenticated user."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value
    
    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must differ from the current one."}
            )
        return attrs
    
    def save(self) -> User:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user

# ─────────────────────────────────────────────────────────────────────────────
# Password — reset request (unauthenticated)
# ─────────────────────────────────────────────────────────────────────────────

class PasswordResetRequestSerializer(serializers.Serializer):
    """Email a reset link to the provided address.
    Always returns 200 ot prevent user enumeration
    """

    email = serializers.EmailField()
    
    def validate_email(self, value: str) -> str:
        self._user = User.objects.filter(email=value.lower().strip(), is_email_verified=True,).first()
        return value
    
    def save(self) -> None:
        if not self._user:
            return # silen no-op
        
        uid = urlsafe_base64_encode(force_bytes(self._user.pk))
        token = default_token_generator.make_token(self._user)
        reset_url = (
            f"{os.environ.get("FRONTEND_URL", 'https://yourapp.com')}"
            f"/reset-password?uid={uid}&token={token}"
        )
        # TODO: send_password_reset_email.delay(self._user.email, reset_url)

    
# ─────────────────────────────────────────────────────────────────────────────
# Password — reset confirm (unauthenticated)
# ─────────────────────────────────────────────────────────────────────────────
class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates the uid + token from the reset link and sets a new password."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        try:
            user_pk = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_pk)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({"uid": "Invalid or malformed reset link."})
        
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": "Reset link is invalid or has already been used"}
            )
        
        attrs["_user"] = user
        return attrs
    
    def save(self) -> User:
        user = self.validated_data["_user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user













 


 
 
# # ─────────────────────────────────────────────────────────────────────────────
# # Google OAuth helpers
# # ─────────────────────────────────────────────────────────────────────────────
 
# def _upsert_google_user(data: dict) -> dict:
#     """
#     Find-or-create a user from Google profile data and return JWT tokens.
#     If the email already exists under EMAIL auth we link Google to that
#     account rather than rejecting, so users can log in with either method.
#     """
#     email = data["email"].lower().strip()
 
#     user, created = User.objects.get_or_create(
#         email=email,
#         defaults={
#             "first_name":        data["first_name"],
#             "last_name":         data["last_name"],
#             "avatar_url":        data["avatar_url"],
#             "auth_provider":     User.AuthProvider.GOOGLE,
#             "is_email_verified": True,
#             "is_active":         True,
#             "auth_status":       "DONE",
#         },
#     )
 
#     if not created:
#         update_fields = []
#         if data["avatar_url"] and not user.avatar:
#             user.avatar_url = data["avatar_url"]
#             update_fields.append("avatar_url")
#         if user.auth_provider != User.AuthProvider.GOOGLE:
#             user.auth_provider = User.AuthProvider.GOOGLE
#             update_fields.append("auth_provider")
#         if update_fields:
#             user.save(update_fields=update_fields)
 
#     return {**_issue_tokens(user), "created": created}
 
 
# # ─────────────────────────────────────────────────────────────────────────────
# # Google OAuth — SPA / mobile  (client sends ID token directly)
# # ─────────────────────────────────────────────────────────────────────────────
 
# class GoogleOAuthSerializer(serializers.Serializer):
#     """Validates a Google ID token and creates or logs in the user."""
 
#     id_token = serializers.CharField()
 
#     def validate_id_token(self, value: str) -> str:
#         try:
#             from google.oauth2 import id_token as google_id_token
#             from google.auth.transport import requests as google_requests
 
#             idinfo = google_id_token.verify_oauth2_token(
#                 value,
#                 google_requests.Request(),
#                 os.environ.get("GOOGLE_CLIENT_ID"),
#             )
#         except Exception:
#             raise serializers.ValidationError(
#                 "Google token is invalid or has expired. Please sign in again."
#             )
 
#         if not idinfo.get("email_verified"):
#             raise serializers.ValidationError(
#                 "The Google account's email address is not verified."
#             )
 
#         self._google_data = {
#             "email":      idinfo["email"],
#             "first_name": idinfo.get("given_name", ""),
#             "last_name":  idinfo.get("family_name", ""),
#             "avatar_url": idinfo.get("picture", ""),
#         }
#         return value
 
#     def save(self) -> dict:
#         return _upsert_google_user(self._google_data)
 
 
# # ─────────────────────────────────────────────────────────────────────────────
# # Google OAuth — server-side  (backend exchanges authorization code)
# # ─────────────────────────────────────────────────────────────────────────────
 
# class GoogleOAuthCallbackSerializer(serializers.Serializer):
#     """Accepts the authorization code from the consent screen and exchanges it."""
 
#     code         = serializers.CharField()
#     redirect_uri = serializers.CharField()
 
#     def validate(self, attrs: dict) -> dict:
#         response = http_requests.post(
#             "https://oauth2.googleapis.com/token",
#             data={
#                 "code":          attrs["code"],
#                 "client_id":     os.environ.get("GOOGLE_CLIENT_ID"),
#                 "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
#                 "redirect_uri":  attrs["redirect_uri"],
#                 "grant_type":    "authorization_code",
#             },
#             timeout=10,
#         )
 
#         if response.status_code != 200:
#             raise serializers.ValidationError(
#                 "Failed to exchange the authorization code with Google."
#             )
 
#         id_token_value = response.json().get("id_token")
#         if not id_token_value:
#             raise serializers.ValidationError("Google did not return an ID token.")
 
#         inner = GoogleOAuthSerializer(data={"id_token": id_token_value})
#         inner.is_valid(raise_exception=True)
 
#         attrs["_google_data"] = inner._google_data
#         return attrs
 
#     def save(self) -> dict:
#         return _upsert_google_user(self.validated_data["_google_data"])




















        

# User Profile:
#
# UserProfileSerializer - Views and edits basic user profile information
# UserDetailSerializer - Returns complete user data with nested relationships (addresses, cards, orders)
# UserPublicSerializer - Shows limited public user info for reviews and messages
# UserUpdateSerializer - Updates user profile fields (name, phone, etc.)
# UserAvatarUpdateSerializer - Uploads and updates user profile picture
# UserDeleteSerializer - Deletes or deactivates user account
# UserStatsSerializer - Returns user statistics (orders, spending, reviews)
# UserActivitySerializer - Shows recent user activity (orders, reviews, views)
#




# ═════════════════════════════════════════════════════════════════════════════
# USER PROFILE
# ═════════════════════════════════════════════════════════════════════════════

class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only view of the authenticated user's own basic profile.
    Returned on GET /accounts/me
    """

    avatar_url  = serializers.SerializerMethodField()
    full_name   = serializers.SerializerMethodField()
    is_seller   = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", 'email', 'username', 'first_name', 'last_name', 'full_name', 
            'phone_number', 'date_of_birth', 'avatar_url', 'is_seller', 
            'is_email_verified', 'auth_provider', 'date_joined', 'updated_at',
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj: User) -> str | None:
        return obj.get_avatar_url()
    
    def get_full_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()

# ─────────────────────────────────────────────────────────────────────────────

class UserAddressListSerializer(serializers.ModelSerializer):
    """Lightweight address entry used inside UserDetailSerializer and list views."""

    class Meta:
        model = UserAddress
        fields = [
            'id', 'address_type', 'full_name', 'address_line_1', 'city', 'country', 'is_default',
        ]
        read_only_fields = fields

# ───────────────────────────────────────────────────────────────────────────── 

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Complete user record with nested relationships.
    Returned on GET /accounts/me/detail/
    Intended for the account-settings page where all data is needed in one call
    """
    
    avatar_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    addresses = UserAddressListSerializer(source='user_address', many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'avatar_url', 
            'is_seller', 'is_email_verified', 'is_mfa_enabled', 'auth_provider', 
            'last_login_at', 'last_login_ip', 'date_joined', 'updated_at', 'addresses',
        ]
        read_only_fields = fields
    
    def get_avatar_url(self, obj: User) -> str | None:
        return obj.get_avatar_url()

    def get_full_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()
    
# ───────────────────────────────────────────────────────────────────────────── 

class UserPublicSerializer(serializers.ModelSerializer):
    """
    Limited public info exposed in review cards, messaging threads, etc/
    Never exposes PII beyond waht a buyer needs to see.
    """

    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    member_since = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar_url', 'member_since', 'is_seller']
        read_only_fields = fields

    def get_avatar_url(self, obj: User) -> str | None:
        return obj.get_avatar_url()
    
    def get_display_name(self, obj: User) -> str:
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or obj.username
    

# ─────────────────────────────────────────────────────────────────────────────

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Updates mutable profile fields
    PATCH /accounts/me/update/
    All fields are optional (partial uodate)
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'date_of_birth', 'username']
        extra_kwargs = {f: {'required': False} for f in fields}
    
    def validate_username(self, value: str) -> str:
        qs = User.objects.filter(username=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def update(self, instance: User, validated_data: dict) -> User:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    


# ─────────────────────────────────────────────────────────────────────────────
class UserAvatarUpdateSerializer(serializers.ModelSerializer):
    """
    handles avatar file upload
    PATCH /accounts/me/avatar/
    Accepts multipart/form-data with field name 'avatar'.
    """

    avatar = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']
    
    def update(self, instance: User, validated_data: dict) -> User:
        # Delete old file to avoid orphaned uploads
        if instance.avatar:
            instance.avatar.delete(save=False)
        instance.avatar = validated_data["avatar"]
        instance.avatar_url = None # clear any OAuth url now that we have a real file
        instance.save(update_fields=['avatar', 'avatar_url'])
        return instance
    


# ────────────────────────────────────────────────────────────────────────────
class UserDeleteSerializer(serializers.Serializer):
    """
    Deactivates (soft-delete) or permanently deletes an account.
    DELETE /accounts/me/delete/
    
    Requires the user's current password for confirmation.
    'hard_delete' defaults to False (deactivation); pass True only if your
    platform policy permits permanent deletion.
    """

    password = serializers.CharField(write_only=True)
    hard_delete = serializers.BooleanField(default = False)

    def validate_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value
    
    def save(self) -> None:
        user = self.context['request'].user
        if self.validated_data['hard_delete']:
            user.delete()
        else:
            user.is_active = False
            user.save(update_fields=['is_active'])



# ────────────────────────────────────────────────────────────────────────────

class UserStatsSerializer(serializers.Serializer):
    """
    Read-only aggregated statistics for the authenticated user.
    GET /accounts/me/stats/
    Counts are computer dynamically; and select_related / prefetch in the view
    for production performance
    """

    total_orders    = serializers.SerializerMethodField()
    total_reviews   = serializers.SerializerMethodField()
    total_addresses = serializers.SerializerMethodField()
    member_for_days = serializers.SerializerMethodField()

    class Meta:
        # not a modelserializer - the view passes the User instance as object
        pass

    def get_total_orders(self, obj: User) -> int:
        return obj.orders.count()
    
    def get_total_addresses(self, obj: User) -> int:
        return obj.user_address.count()
    
    def get_member_for_days(self, obj: User) -> int:
        return (timezone.now() - obj.date_joined).days
    
    def to_representation(self, instance: User) -> dict:
        return {
            'total_orders': self.get_total_orders(instance),
            'total_addresses': self.get_total_addresses(instance),
            'member_for_days': self.get_member_for_days(instance),
        }

# ─────────────────────────────────────────────────────────────────────────────

class UserActivitySerializer(serializers.Serializer):
    """
    Recent activity feed for the authenticated user.
    GET /accounts/me/activity/
    
    Each activity item is a dict with: type, description, timestamp.
    Plug in real querysets from orders / reviews/ products as those apps grow
    """

    def to_representation(self, instance: User) -> dict:
        activities = []

        for addr in instance.user_address.order_by("-created_at")[:3]:
            activities.append({
                'type': 'address_added',
                'description': f"Added address: {addr.address_line_1}, {addr.city}",
                'timestamp': addr.created_at,
            })

        # ── Placeholder hooks for future apps ────────────────────────────────
        
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return {'activites': activities[:10]}
 
 
 


















# # User Addresses:
# #
# # UserAddressSerializer - CRUD operations for single address
# # UserAddressListSerializer - Lists all user addresses with minimal fields
# # UserAddressCreateSerializer - Creates new shipping/billing address
# # UserAddressUpdateSerializer - Updates existing address details
# # UserAddressDeleteSerializer - Deletes user address
# # SetDefaultAddressSerializer - Sets address as default for shipping/billing


# # ═════════════════════════════════════════════════════════════════════════════
# # USER ADDRESSES
# # ═════════════════════════════════════════════════════════════════════════════

class UserAddressSerializer(serializers.ModelSerializer):
    """
    Full address detail. 
    GET /accounts/me/addresses/<id>/
    """

    class Meta:
        model = UserAddress
        fields = [
            'id', 'address_type', 'full_name', 'phone_number',
            'address_line_1', 'address_line_2',
            'city', 'state_province', 'postal_code', 'country',
            'is_default', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# # ─────────────────────────────────────────────────────────────────────────────

class UserAddressCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new address for the authenticated user.
    POST /accounts/me/addresses/
    
    If this is the user's first address, it is automatically set as default.
    If 'is_default' is True, any existing default is demoted.
    """

    class Meta:
        model = UserAddress
        fields = [
            'address_type', 'full_name', 'phone_number', 'address_line_1', 
            'address_line_2', 'city', 'state_province', 'postal_code', 'country', 
            'is_default', 
        ]

    @transaction.atomic
    def create(self, validated_data: dict) -> UserAddress:
        user = self.context["request"].user
        is_default = validated_data.get('is_default', False)

        # first address is always default
        if not UserAddress.objects.filter(user=user).exists():
            validated_data['is_default'] = True
        elif is_default:
            UserAddress.objects.filter(user=user, is_default=True).update(is_default=False)
        return UserAddress.objects.create(user=user, **validated_data)
    

# # ─────────────────────────────────────────────────────────────────────────────

class UserAddressUpdateSerializer(serializers.ModelSerializer):
    """
    Updates an existing address.
    PATCH /accounts/me/addresses/<id>/
    All fields optional
    """

    class Meta:
        model = UserAddress
        fields = [
            'address_type', 'full_name', 'phone_number', 
            'address_line_1', 'address_line_2',
            'city', 'state_province', 'postal_code', 'country', 
        ]
        extra_kwargs = {f: {'required': False} for f in fields}

        @transaction.atomic
        def update(self, instance: UserAddress, validated_data: dict) -> UserAddress:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        



 
 
# # ─────────────────────────────────────────────────────────────────────────────

class UserAddressDeleteSerializer(serializers.Serializer):
    """
    Validates that the address can be safely deleted.
    DELETE /accounts/me/addresses/<id>/
    
    Prevents deleting a default address when other addresses still exists,
    so the user is never left without a usable default.
    """

    address_id = serializers.IntegerField()

    def validate_address_id(self, value: int) -> int:
        user = self.context['request'].user
        address = _get_own_address(user, value)

        if address.is_default:
            other_count = UserAddress.objects.filter(user=user).exclude(pk=value).count()
            if other_count > 0:
                raise serializers.ValidationError(
                    "Cannot delete the default address while other addresses exist." \
                    "Please set another address as default first."
                )
        self._address = address
        return value
    
    def save(self) -> None:
        self._address.delete()
        
            
# # ─────────────────────────────────────────────────────────────────────────────

class SetDefaultAddressSerializer(serializers.Serializer):
    """
    Sets a given address as the default for the authenticated user
    PATCH /accounts/me/addresses/<id>/set-default/
    
    Atomically demotes the previous default and promotes the new one.
    """
    address_id = serializers.IntegerField()
    
    def validate_address_id(self, value: int) -> int:
        user = self.context['request'].user
        self._address = _get_own_address(user, value)
        return value
    
    @transaction.atomic
    def save(self) -> UserAddress:
        user = self.context['request'].user
        UserAddress.objects.filter(user=user, is_default=True).update(is_default=False)
        self._address.is_default = True
        self._address.save(update_fields=['is_default'])
        return self._address