from django.db import models
from uuid import uuid4
import random
from datetime import timedelta
import time
from django.utils.timezone import now
from django.contrib.auth import models, hashers

class User(models.AbstractUser):
    AUTH_STATUS = (
        ('NEW', 'New'),
        ('REGISTERED', 'Registered')
        ('DONE', 'Done')
    )
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phone_number = models.CharField(max_length=50, null=True)
    date_of_birth = models.DateField(null= True, blank = True,)
    profile_picture = models.ImageField(upload_to="profile_photos/", null = True, blank=True)
    is_seller = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.username
    
    def generate_code(self):
        base = random.randint(10000, 99999)
        noise = time.time_ns()%1000
        c3 = (base^noise)%100000
        code = str(c3).zfill(5)
        EmailVerification.objects.filter(user=self, is_verified=False).delete()
        EmailVerification.objects.filter(user=self, code=code)
        return code
    
    def generate_username(self):
        return f"user_{uuid4().hex[:8]}"
    
    def check_username(self):
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
    
    def check_email(self):
        if self.email:
            self.email = self.email.lower()

    def can_resend_code(self):
        last_code = EmailVerification.objects.filter(user=self, confirmed=False).order_by('-created_at').first()
        if not last_code:
            return True
        time_passed = now() - last_code.created_at
        return time_passed.total_seconds() > 180

    def save(self, *args, **kwargs):
        self.generate_username()
        return super().save(*args, **kwargs)
    


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_codes")
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
        return now() > self.expiration_time
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.expiration_time = now() + timedelta(minutes = 3)
        super().save(*args, **kwargs)



class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,help_text="owner of address", related_name="user_address")
    address_type = models.CharField(max_length=20, help_text="'shipping', 'billing', 'both'")
    full_name = models.CharField(max_length=200, help_text="Recepient name")
    phone_number = models.CharField(max_length=20, help_text="Contact phone")
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
    

