
"""
Full URL map
─────────────────────────────────────────────────────────────────
USER PROFILE
  GET     /accounts/me/                       own basic profile
  GET     /accounts/me/detail/                full profile + nested data
  PATCH   /accounts/me/update/                update name / phone / dob
  PATCH   /accounts/me/avatar/                upload new avatar
  DELETE  /accounts/me/delete/                deactivate or hard-delete
  GET     /accounts/me/stats/                 order / review counts etc.
  GET     /accounts/me/activity/              recent activity feed
  GET     /accounts/users/<username>/         public profile of any user
 
SELLER
  POST    /accounts/me/become-seller/         convert user → seller
  GET     /accounts/me/seller/                own full seller profile
  PATCH   /accounts/me/seller/update/         update seller info / logo
  GET     /accounts/me/seller/stats/          performance dashboard
  GET     /accounts/sellers/<seller_id>/      public seller card (no auth)
 
ADDRESSES
  GET     /accounts/me/addresses/             list all addresses
  POST    /accounts/me/addresses/             create address
  GET     /accounts/me/addresses/<id>/        retrieve single address
  PATCH   /accounts/me/addresses/<id>/        update address
  DELETE  /accounts/me/addresses/<id>/        delete address
  PATCH   /accounts/me/addresses/<id>/set-default/  promote to default
─────────────────────────────────────────────────────────────────
"""




from django.urls import path
from .views import *
from .seller_views import *



urlpatterns = [
    # ── Registration (3 steps) ──────────────────────────────────────────────
    path("register/",          RegisterEmailView.as_view(),   name="account-register"),
    path("verify-email/",      VerifyEmailView.as_view(),     name="account-verify-email"),
    path("complete-profile/<uuid:user_id>/", CompleteProfileView.as_view(), name="account-complete-profile"),

    # ── Session ─────────────────────────────────────────────────────────────
    path("login/",             LoginView.as_view(),           name="account-login"),
    path("logout/",            LogoutView.as_view(),          name="account-logout"),


    # ── Tokens ─────────────────────────────────────────────────────────────
    path("token/refresh/",     TokenRefreshView.as_view(),     name="account-token-refesh"),


    # ── OTP helpers ─────────────────────────────────────────────────────────────
    path("resend-otp/",        ResendOTPView.as_view(),       name="account-resend-otp"),

    
    # ── Password ─────────────────────────────────────────────────────────────
    path("password/change/",        PasswordChangeView.as_view(),       name="account-password-change"),
    path("password/reset/",         PasswordResetRequestView.as_view(), name="account-password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="account-password-reset-confirm"),


    # ── Google OAuth ─────────────────────────────────────────────────────────────


    # ── User profile ─────────────────────────────────────────────────────────────
    path("me/",               UserProfileView.as_view(),      name="account-me"),
    path("me/detail/",        UserDetailView.as_view(),       name="account-me-detail"),
    path("me/update/",        UserUpdateView.as_view(),       name="account-me-update"),
    path("me/delete/",        UserDeleteView.as_view(),       name="account-me-delete"),
    path("me/stats/",         UserStatsView.as_view(),        name="account-me-stats"),
    path("me/avatar/update/", UserAvatarUpdateView.as_view(), name="account-me-avatar"),
    path("me/activity/",      UserActivityView.as_view(),     name="account-me-activity"),


    # ── Public user profile ───────────────────────────────────────────────────
    path("users/<str:username>/", UserPublicView.as_view(),   name="account-public"),
    

    # ── Addresses ────────────────────────────────────────────────────────────
    path('me/addresses/',                           UserAddressListCreateView.as_view(), name='address-list-create'),
    path('me/addresses/<int:pk>/',                  UserAddressDetailView.as_view(),     name='address-detail'),
    path('me/addresses/<int:pk>/set-default/',      SetDefaultAddressView.as_view(),     name='address-set-default'),



    # ── Become seller / seller profile ───────────────────────────────────────
    path("me/become-seller/",           BecomeSellerView.as_view(),         name="become-seller"),
    path("me/seller/",                  SellerProfileView.as_view(),        name="seller-profile"),
    path("me/seller/update/",           SellerProfileUpdateView.as_view(),  name="seller-profile-update"),
    path("sellers/<int:seller_id>/",    SellerPublciView.as_view(),         name="seller-public"),
    path("me/seller/stats/",            SellerStatsView.as_view(),          name="seller-stats"),








]