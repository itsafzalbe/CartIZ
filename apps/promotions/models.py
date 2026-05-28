from django.db import models
from apps.stores.models import Market
from apps.orders.models import Order
from apps.accounts.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from apps.products.models import Product

# Create your models here.








# COUPON
# COUPON_USAGE



class Coupon(models.Model):
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed_amount'

    DISCOUNT_TYPE = (
        (PERCENTAGE, 'Percentage'),
        (FIXED_AMOUNT, 'Fixed amount'),
    )
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="coupons")
    code = models.CharField(max_length=50, unique=True, help_text="Coupon code")
    description = models.TextField(null=True, blank=True, help_text="Coupon description")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, validators=[MinValueValidator(0)], decimal_places=2, help_text="Discount amount/percentage")
    min_purchase_amount = models.DecimalField(max_digits=10, validators=[MinValueValidator(0)], blank=True, null=True, decimal_places=2, help_text="Minimum order value")
    max_discount_amount = models.DecimalField(max_digits=10, validators=[MinValueValidator(0)], blank=True, null=True, decimal_places=2, help_text="Maximum discount cap")
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total usage limit")
    usage_count = models.PositiveIntegerField(default=0, help_text="Times used")
    per_user_limit = models.PositiveIntegerField(default=1, help_text='Uses per user')
    valid_from = models.DateTimeField(help_text="Start date")
    valid_until = models.DateTimeField(help_text="End date")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coupons"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["market"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["valid_until"]),
        ]
    
    def __str__(self):
        return f"{self.code}  ({self.market})"
    
    def clean(self):
        if self.valid_until <= self.valid_from:
            raise ValidationError("Valid until should be after valid from")


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="usages")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="coupon_usages")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coupon_usages")
    discount_amount = models.DecimalField(decimal_places=2, validators=[MinValueValidator(0)], max_digits=10, help_text="Discount applied")
    used_at = models.DateTimeField(auto_now_add=True, help_text="Usage timestamp")

    class Meta:
        db_table = "coupon_usages"
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        ordering = ["-used_at"]
        indexes = [
            models.Index(fields=["coupon"]),
            models.Index(fields=["user"]),
            models.Index(fields=["coupon", "user"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["coupon", "order"],
                name="unique_coupon_usage_per_order"
            )
        ]
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.user} on Order #{self.order.pk}"




# ─────────────────────────────────────────────────────────────────────────────
# FLASH SALE
# ─────────────────────────────────────────────────────────────────────────────
 
class FlashSale(models.Model):
    market          = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='flash_sales')
    title           = models.CharField(max_length=255)
    description     = models.TextField(null=True, blank=True)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(1)],
        help_text='Percentage discount applied to all sale products',
    )
    products = models.ManyToManyField('products.Product', related_name='flash_sales', blank=True)
    starts_at       = models.DateTimeField()
    ends_at         = models.DateTimeField()
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table            = 'flash_sales'
        verbose_name        = 'Flash Sale'
        verbose_name_plural = 'Flash Sales'
        ordering            = ['-starts_at']
        indexes             = [
            models.Index(fields=['is_active']),
            models.Index(fields=['starts_at', 'ends_at']),
        ]
 
    def __str__(self):
        return f"{self.title} ({self.market})"
 
    def clean(self):
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            raise ValidationError('ends_at must be after starts_at.')
 
    @property
    def is_live(self):
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at
 
    @property
    def is_upcoming(self):
        return timezone.now() < self.starts_at
 
    @property
    def is_ended(self):
        return timezone.now() > self.ends_at
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PROMOTION
# ─────────────────────────────────────────────────────────────────────────────
 
class Promotion(models.Model):
    BANNER   = 'banner'
    DISCOUNT = 'discount'
    BUNDLE   = 'bundle'
    SEASONAL = 'seasonal'
    CLEARANCE = 'clearance'
 
    PROMOTION_TYPE = (
        (BANNER,    'Banner'),
        (DISCOUNT,  'Discount'),
        (BUNDLE,    'Bundle'),
        (SEASONAL,  'Seasonal'),
        (CLEARANCE, 'Clearance'),
    )
 
    market       = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='promotions', null=True, blank=True)
    title        = models.CharField(max_length=255)
    description  = models.TextField(null=True, blank=True)
    promo_type   = models.CharField(max_length=20, choices=PROMOTION_TYPE, default=DISCOUNT)
    image        = models.ImageField(upload_to='promotions/', null=True, blank=True)
    products     = models.ManyToManyField(Product, related_name='promotions', blank=True)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    starts_at    = models.DateTimeField()
    ends_at      = models.DateTimeField()
    is_active    = models.BooleanField(default=True)
    is_featured  = models.BooleanField(default=False)
    view_count   = models.PositiveIntegerField(default=0)
    click_count  = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table            = 'promotions'
        verbose_name        = 'Promotion'
        verbose_name_plural = 'Promotions'
        ordering            = ['-created_at']
        indexes             = [
            models.Index(fields=['is_active']),
            models.Index(fields=['promo_type']),
            models.Index(fields=['starts_at', 'ends_at']),
        ]
 
    def __str__(self):
        return self.title
 
    def clean(self):
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            raise ValidationError('ends_at must be after starts_at.')
 
    @property
    def is_live(self):
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at
 
    @property
    def is_upcoming(self):
        return timezone.now() < self.starts_at
 
    @property
    def is_ended(self):
        return timezone.now() > self.ends_at