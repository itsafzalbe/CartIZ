from django.contrib import admin
from .models import User, EmailVerification, UserAddress


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "phone_number", "is_seller", "is_verified", "created_at")
    search_fields = ("username", "email")
    list_filter = ("is_seller", "is_verified")
    ordering = ("-created_at",)


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "confirmed", "expiration_time", "created_at")
    search_fields = ("user__email", "confirmed")
    list_filter = ("confirmed", )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "country", "is_default", "created_at")
    search_fields = ("full_name", "city", "country", "user__email")
    list_filter = ("country", "is_default")
