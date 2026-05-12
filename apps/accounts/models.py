from django.db import models
import uuid
import random
from datetime import timedelta
import time
from django.utils import timezone
from django.contrib.auth import hashers
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
 

OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_RESENDS = 5

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('SuperUser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('SuperUser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class AuthProvider(models.TextChoices):
        EMAIL = 'email', _('Email')
        GOOGLE = 'google', _('Google')

    AUTH_STATUS = (
        ('NEW', 'New'),
        ('REGISTERED', 'Registered'),
        ('DONE', 'Done')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=50, validators=[RegexValidator(r'^\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', 'Enter valid phone number')], null=True)
    email = models.EmailField(unique=True, db_index=True, max_length=255)
    auth_status = models.CharField(max_length=20, choices=AUTH_STATUS, default='NEW')
    date_of_birth = models.DateField(null= True, blank = True,)
    avatar = models.ImageField(upload_to="avatars/", null = True, blank=True)
    avatar_url = models.URLField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_mfa_enabled = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)

    auth_provider = models.CharField(max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL)

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_seller']),
            models.Index(fields=['date_joined']),
        ]

    def __str__(self):
        return self.email
    
    @property
    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return self.avatar_url or None
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def generate_code(self):
        base = random.randint(10000, 99999)
        noise = time.time_ns()%1000
        c3 = (base^noise)%100000
        code = str(c3).zfill(5)
        EmailVerification.objects.filter(user=self, confirmed=False).delete()
        return code
    
    @staticmethod
    def generate_username():
        return f"user_{uuid.uuid4().hex[:8]}"
    
    def ensure_username(self):
        if not self.username:
            username = self.generate_username()
            while User.objects.filter(username=username).exists():
                username = self.generate_username()
            self.username=username
    
    def hashing_pass(self):
        if self.password:
            try:
                hashers.identify_hasher(self.password)
            except ValueError:
                self.set_password(self.password)
    
    def clean_email(self):
        if self.email:
            self.email = self.email.lower()

    def hashing_pas(self):
        if self.password:
            try:
                hashers.identify_hasher(self.password)
            except ValueError:
                self.set_password(self.password)

    def can_resend_code(self):
        last_code = EmailVerification.objects.filter(user=self, confirmed=False).order_by('-created_at').first()
        if not last_code:
            return True
        time_passed = timezone.now() - last_code.created_at
        return time_passed.total_seconds() > OTP_RESEND_COOLDOWN_SECONDS

    def save(self, *args, **kwargs):
        self.ensure_username()
        self.clean_email()
        super().save(*args, **kwargs)
    


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=5)
    expiration_time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verification'
        verbose_name = "Email Verification"
        verbose_name_plural = "Email Verifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.code}"
    
    def is_expired(self):
        return timezone.now() > self.expiration_time
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.expiration_time = timezone.now() + timedelta(minutes = 3)
        super().save(*args, **kwargs)



class UserAddress(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
        ('both', 'Both'),
    )


    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Owner of address", related_name="user_address")
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, help_text="'shipping', 'billing', 'both'")
    full_name = models.CharField(max_length=200, help_text="Recipient name")

    phone_number = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', 'Enter valid phone number')], help_text="Contact phone")
    address_line_1 = models.CharField(max_length=255, help_text="Street address")
    address_line_2 = models.CharField(max_length=255, null=True, blank=True, help_text="Apartment, suite, etc.")
    city = models.CharField(max_length=100, help_text="City name")
    state_province = models.CharField(max_length=100, help_text="State/Province")
    postal_code = models.CharField(max_length=20, help_text="ZIP/Postal code")
    country = models.CharField(max_length=100, help_text="Country name")
    is_default = models.BooleanField(default=False, help_text="Default address flag")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.address_line_1}"
    