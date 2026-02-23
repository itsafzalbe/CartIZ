from django.db import models
from accounts.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator





# MARKET
# MARKET_REVIEW

class Market(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='markets')
    market_name = models.CharField(max_length=255, validators=[RegexValidator(r'^[A-Za-z0-9]+(?: [A-Za-z0-9]+)*$', 'Enter valid name')], unique=True, help_text="Store name")
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True, help_text="Store description")
    logo = models.ImageField(upload_to='seller/market/logos/', null=True, blank=True, help_text="Store logo image")
    banner_image = models.ImageField(upload_to='seller/market/banners/', null=True, blank=True, help_text="Store banner image")
    business_email = models.EmailField(null=True, blank=True, help_text="Business contact email")
    business_phone = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', 'Enter valid phone number')], help_text="Business phone number")
    business_address = models.TextField(null=True, blank=True, help_text="Physical store address")
    tax_id = models.CharField(max_length=50, null=True, blank=True, help_text="Business tax ID")
    is_verified = models.BooleanField(default=False, help_text="Verified seller status")
    is_active = models.BooleanField(default=True, help_text="Store active status")
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)], default=0, help_text="Average rating (0-5)")
    total_sales = models.PositiveIntegerField(help_text="Total number of sales")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Store creation date")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")

    class Meta:
        db_table = "markets"
        verbose_name = "Market"
        verbose_name_plural = "Markets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['seller'])
        ]

    def __str__(self):
        return self.market_name


    def save(self, *args, **kwargs):
        if self.market_name:
            self.market_name = " ".join(self.market_name.split()).title()
        if not self.slug:
            base_slug = slugify(self.market_name)
            slug = base_slug
            counter = 1

            while Market.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)



class MarketReview(models.Model):
    market_id
    user_id
    order_id
    rating
    comment
    is_approved
    created_at
    updated_at









