from rest_framework import serializers
from .models import *


#
# 1. ACCOUNTS APP (40 serializers)Authentication & Registration:
#
# UserRegistrationSerializer - Handles new user signup with email, username, and password
# UserLoginSerializer - Authenticates user credentials and returns auth tokens
# UserLogoutSerializer - Invalidates refresh token and logs user out
# PasswordChangeSerializer - Changes password for authenticated users
# PasswordResetRequestSerializer - Sends password reset link to user's email
# PasswordResetConfirmSerializer - Resets password using token from email
# EmailVerificationSerializer - Verifies user email address with token
# ResendVerificationEmailSerializer - Resends email verification link
# RefreshTokenSerializer - Generates new access token from refresh token
#
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
# Become Seller:
#
# BecomeSellerSerializer - Converts regular user to seller with business information
# SellerProfileSerializer - Views and edits seller business details
# SellerProfileUpdateSerializer - Updates seller business information
# SellerPublicSerializer - Shows public seller info visible to buyers
# SellerStatsSerializer - Returns seller performance metrics and analytics
#
# User Addresses:
#
# UserAddressSerializer - CRUD operations for single address
# UserAddressListSerializer - Lists all user addresses with minimal fields
# UserAddressCreateSerializer - Creates new shipping/billing address
# UserAddressUpdateSerializer - Updates existing address details
# UserAddressDeleteSerializer - Deletes user address
# SetDefaultAddressSerializer - Sets address as default for shipping/billing
