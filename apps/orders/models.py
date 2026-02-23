from django.db import models
from accounts.models import User
from stores.models import Market
from django.core.validators import MinValueValidator
from django.db.models import GenericIPAddressField, Q
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from products.models import *

# ORDER
# ORDER_ITEM
# ORDER_ADDRESS
# ORDER_SHIPPING
# SHIPPING_METHOD


class Order(models.Model):
    ORDER_PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    ORDER_REFUNDED = 'refunded'

    STATUS_CHOICES = (
        (ORDER_PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (PROCESSING, 'Processing'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
        (ORDER_REFUNDED, 'Refunded'),
    )

    PAYMENT_PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    PAYMENT_REFUNDED = 'refunded'

    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_PENDING, 'Pending'),
        (PAID, 'Paid'),
        (FAILED, 'Failed'),
        (PAYMENT_REFUNDED, 'Refunded'),
    )
    order_number = models.CharField(max_length=50, unique=True, help_text="Human-readable order number")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    market = models.ForeignKey(Market, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ORDER_PENDING)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Items total")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Tax amount")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Shipping fee")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Total discount")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Final total")
    currency = models.CharField(max_length=3, default='USD', db_index=True, help_text="Currency code")
    notes = models.TextField(null=True, blank=True, help_text="Customer notes")
    admin_notes = models.TextField(null=True, blank=True, help_text="Internal notes")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="Customer IP")
    user_agent = models.TextField(null=True, blank=True, help_text="Browser info")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Order creation time")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last status update")
    paid_at = models.DateTimeField(null=True, blank=True, help_text="Payment timestamp")
    shipped_at = models.DateTimeField(null=True, blank=True, help_text="Shipping timestamp")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="Delivery timestamp")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="Cancellation timestamp")


    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['market', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['payment_status']),
        ]

    def clean(self):
        expected_total = (self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount)
        if expected_total < 0:
            raise ValidationError("Total cannot be negative")
        if self.total_amount.quantize(Decimal("0.01")) != expected_total.quantize(Decimal("0.01")):
            raise ValidationError({'total_amount': f"Total must equal {expected_total}"})
        
    def save(self, *args, **kwargs):
        if self.status == self.SHIPPED and not self.shipped_at:
            self.shipped_at = timezone.now()
        
        if self.status == self.DELIVERED and not self.delivered_at:
            self.delivered_at = timezone.now()
        
        if self.status == self.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        
        if self.payment_status == self.PAID and not self.paid_at:
            self.paid_at = timezone.now()
        
        if self.currency:
            self.currency = self.currency.upper()

        self.full_clean()
        super().save(*args, **kwargs)



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True, related_name="order_items")
    product_name = models.CharField(max_length=255, help_text="Product name at purchase")
    variant_name = models.CharField(max_length=255, null=True, blank=True, help_text="Variant details" )
    sku = models.CharField(max_length=100, help_text="SKU at purchase")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Ordered quantity")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Price per unit")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Quantity x unit_price")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Item discount")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Tax for this item") 
    total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Final item total")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'variant'],
                condition=Q(variant__isnull=False),
                name="unique_variant_per_order"
            ),
            models.UniqueConstraint(
                fields=['order', 'product'],
                condition=Q(variant__isnull=True),
                name="unique_product_per_order"
            ),
            models.CheckConstraint(
                check=Q(total__gte=0),
                name="orderitem_total_non_negative" 
            ),
        ]

    def clean(self):
        if self.variant and self.variant.product_id != self.product_id:
            raise ValidationError("Variant does not belong to the product.")
        expected_subtotal = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        expected_total = (expected_subtotal - self.discount + self.tax_amount).quantize(Decimal("0.01"))

        if expected_total < 0:
            raise ValidationError("Total cannot be negative.")

        if self.subtotal.quantize(Decimal("0.01")) != expected_subtotal:
            raise ValidationError({"subtotal": "Subtotal mismatch."})
        
        if self.total.quantize(Decimal("0.01")) != expected_total:
            raise ValidationError({"total": "Total mismatch."})
    
    def save(self, *args, **kwargs):
        self.subtotal = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        self.total = (self.subtotal - self.discount + self.tax_amount).quantize(Decimal("0.01"))
        self.full_clean()
        super().save(*args, **kwargs)

        





class OrderAddress(models.Model):
    SHIPPING = 'shipping' 
    BILLING = 'billing'
    ADDRESS_CHOICES = (
        (SHIPPING, "Shipping"),
        (BILLING, "Billing"),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=20, choices=ADDRESS_CHOICES)
    full_name = models.CharField(max_length=200, help_text="Recipient name")
    phone_number = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', 'Enter valid phone number')], help_text="Contact phone")
    address_line_1 = models.CharField(max_length=255, help_text="Street address")
    address_line_2 = models.CharField(max_length=255, null=True, blank=True, help_text="Apartment, suite, etc.")
    city = models.CharField(max_length=100, help_text="City name")
    state_province = models.CharField(max_length=100, help_text="State/Province")
    postal_code = models.CharField(max_length=100, help_text="ZIP/Postal code")
    country = models.CharField(max_length=100, help_text="Country name")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_addresses"
        verbose_name = "Order Address"
        verbose_name_plural = "Order Addresses"
        indexes = [
            models.Index(fields=['order']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'address_type'],
                name="unique_address_type_per_order"
            )
        ]
    
    def svae(self, *args, **kwargs):
        if self.full_name:
            self.full_name = self.full_name.strip().title()
        super().save(*args, **kwargs)






class ShippingMethod(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="shipping_methods")
    name = models.CharField(max_length=200, help_text="Method name")
    description = models.TextField(null=True, blank=True, help_text="Method description")
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Shipping cost")
    estimated_days_min = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(365)], help_text="Min delivery days")
    estimated_days_max = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(365)], help_text="Max delivery days")
    is_active = models.BooleanField(default=True, help_text="Active status")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")

    class Meta:
        db_table = "shipping_methods"
        verbose_name = "Shipping Method"
        verbose_name_plural = "Shipping Methods"
        indexes = [
            models.Index(fields=['market']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['market', 'name'],
                name="unique_shipping_method_per_market"
            )
        ]

    def clean(self):
        if self.estimated_days_min is not None and self.estimated_days_max is not None:
            if self.estimated_days_min > self.estimated_days_max:
                raise ValidationError("Minimum days cannot exceed maximum days.")
        
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().title()
        self.full_clean()
        super().save(*args, **kwargs)

    


class OrderShipping(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipping")
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.PROTECT, related_name="shipments")
    tracking_number = models.CharField(max_length=100, null=True, blank=True, help_text="Tracking number")
    carrier = models.CharField(max_length=100, null=True, blank=True, help_text="Shipping carrier")
    shipped_at = models.DateTimeField(null=True, blank=True, help_text="Ship date")
    estimated_delivery = models.DateTimeField(null=True, blank=True, help_text="Estimated arrival")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="Actual delivery date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_shipping"
        verbose_name = "Order Shipping"
        verbose_name_plural = "Order Shipping"
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['shipped_at']),
        ]
    
    def clean(self):
        if self.shipped_at and self.delivered_at:
            if self.delivered_at < self.shipped_at:
                raise ValidationError("Delivery date cannot be before shipped date.")
        
        if self.shipped_at and self.estimated_delivery:
            if self.estimated_delivery < self.shipped_at:
                raise ValidationError("Estimated delivery cannot be before shipping date.")
        
        if self.delivered_at and not self.shipped_at:
            raise ValidationError("Order must be shipped before delivery.")
        
        if self.tracking_number and not self.carrier:
            raise ValidationError("Carrier is required when tracking number is provided.")
        
        if self.delivered_at and self.delivered_at > timezone.now():
            raise ValidationError("Delivered date cannot be in the future.")
    
    def save(self, *args, **kwargs):
        if self.tracking_number:
            self.tracking_number = self.tracking_number.strip()
        
        if self.tracking_number and not self.shipped_at:
            self.shipped_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)
    













