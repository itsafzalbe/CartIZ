from django.db import models
from apps.stores.models import Market
from apps.orders.models import Order
from apps.accounts.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

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



