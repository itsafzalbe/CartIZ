from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator
from products.models import *
from django.db.models import Q
from django.core.exceptions import ValidationError


# CART
# CART_ITEM


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name="items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Item quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Price at time of adding")
    added_at = models.DateTimeField(auto_now_add=True, help_text="When item was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last quantity update")

    class Meta:
        db_table = "cart_items"
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['cart', 'prod']),
            models.Index(fields=['cart', 'variant']),
            models.Index(fields=['product']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'variant'],
                condition=Q(variant__isnull=False),
                name="unique_variant_per_cart"
            ),
            models.UniqueConstraint(
                fields=['cart', 'product'],
                condition=Q(variant__isnull=True),
                name="unique_product_per_cart"
            ),
        ]
    
    def clean(self):
        #If variant exists, it must belong to the selected product
        if self.variant and self.variant.product_id != self.product_id:
            raise ValidationError("Selected variant does not belong to this product.")
    
    @property
    def total_price(self):
        return self.quantity * self.price
    
    def __str__(self):
        if self.variant:
            return f"{self.variant} x {self.quantity}"
        return f"{self.product} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

