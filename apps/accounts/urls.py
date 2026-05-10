from django.urls import path
from .views import *



urlpatterns = [
    # ── Registration (3 steps) ──────────────────────────────────────────────
    path("register/",          RegisterEmailView.as_view(),   name="auth-register"),
    path("verify-email/",      VerifyEmailView.as_view(),     name="auth-verify-email"),
    path("complete-profile/<uuid:user_id>/", CompleteProfileView.as_view(), name="auth-complete-profile"),

    # ── Session ─────────────────────────────────────────────────────────────
    path("login/",             LoginView.as_view(),           name="auth-login"),
    path("logout/",            LogoutView.as_view(),          name="auth-logout"),


    # ── Tokens ─────────────────────────────────────────────────────────────
    path("token/refresh/",     TokenRefreshView.as_view(),     name="auth-token-refesh"),


    # ── OTP helpers ─────────────────────────────────────────────────────────────
    path("resend-otp/",        ResendOTPView.as_view(),       name="auth-resend-otp"),





]