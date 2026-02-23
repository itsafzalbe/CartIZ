from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from stores.models import Market
from django.utils.text import slugify
from django.db.models import Q
from accounts.models import User
from orders.models import OrderItem
from django.core.exceptions import ValidationError
from django.utils import timezone


# CATEGORY
# PRODUCT
# PRODUCT_IMAGE
# PRODUCT_VARIANT
# PRODUCT_ATTRIBUTE
# PRODUCT_ATTRIBUTE_VALUE
# PRODUCT_REVIEW
# WISHLIST
# WISHLIST_ITEM


class Category(models.Model):
    parent_id = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="Children")
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="category/images/", null=True, blank=True)
    icon = models.CharField(max_length=100, null=True, blank=True)
    order_position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['order_position', 'name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255, help_text="Product name")
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True, help_text="Full product description")
    short_description = models.CharField(max_length=500, null=True, blank=True, help_text="Brief description")
    sku = models.CharField(max_length=100, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=50, help_text="Product barcode")
    price = models.DecimalField(max_digits=10, validators=[MinValueValidator(0)], decimal_places=2, help_text="Current price")
    compare_at_price = models.DecimalField(max_digits=10, validators=[MinValueValidator(0)], null=True, blank=True, decimal_places=2, help_text="Original price (for discounts)")
    cost_price = models.DecimalField(max_digits=10, validators=[MinValueValidator(0)], decimal_places=2, help_text="Cost to seller")
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Available quantity")
    low_stock_threshold = models.PositiveIntegerField(default=10, help_text="Alert threshold")
    weight = models.DecimalField(max_digits=6, null=True, blank=True, decimal_places=2, help_text="Product weight (kg)")
    dimensions = models.CharField(max_length=100, null=True, blank=True, help_text="L x W x H dimensions")
    is_featured = models.BooleanField(default=False, help_text="Featured product flag")
    is_active = models.BooleanField(default=True, help_text="Product active status")
    is_digital = models.BooleanField(default=False, help_text="Digital product flag")
    rating_average = models.DecimalField(max_digits=3, validators=[MinValueValidator(0), MaxValueValidator(5)], decimal_places=2, default=0.00, help_text="Average rating (0-5)")
    review_count = models.PositiveBigIntegerField(default=0, help_text="Total reviews")
    view_count = models.PositiveBigIntegerField(default=0, help_text="Product views")
    sold_count = models.PositiveBigIntegerField(default=0, help_text="Total units sold")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['market', 'sku'],
                name='unique_sku_per_market'
            ),
            models.UniqueConstraint(
                fields=['market', 'barcode'],
                name='unique_barcode_per_market'
            )
        ]
        indexes = [
            models.Index(fields=['market', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['created_at']),
            models.Index(fields=['price']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            discount_percentage = (self.compare_at_price - self.price) / self.compare_at_price * 100
            return round(discount_percentage)
        return 0
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def in_stock(self):
        return self.stock_quantity > 0 


    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, null=True, blank=True, help_text="Image alt text")
    is_primary = models.BooleanField(default=False, help_text="Primary product image")
    order_position = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['order_position']
        constraint = [
            models.UniqueConstraint(
                fields=['product'],
                condition=Q(is_primary=True),
                name='unique_primary_image_per_product'
            )
        ]
    def __str__(self):
        return f"{self.product.name} image"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_variants")
    variant_name = models.CharField(max_length=100, help_text="Variant name (e.g., 'Red-Large')")
    sku = models.CharField(max_length=100, db_index=True, help_text="Variant SKU")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Variant-specific price")
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Variant stock")
    attributes = models.JSONField(null=True, blank=True, help_text="JSON of attributes {color: 'red', size: 'large'}")
    image = models.ImageField(upload_to="products/variants/", null=True, blank=True, help_text="Variant-specific image")
    is_active = models.BooleanField(default=True, help_text="Variant active status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_variants"
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ['variant_name']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'sku'],
                name="unique_variant_sku_per_product"
            )
        ]
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['is_active']),
        ]
    
    @property
    def in_stock(self):
        return self.stock_quantity > 0 
    
    @property
    def low_in_stock(self):
        return self.stock_quantity <= 10 
    
    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Attribute name (e.g., 'Color')")
    slug = models.SlugField(unique=True, help_text="URL-friendly name")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")

    class Meta:
        db_table = "product_attributes"
        verbose_name = "Product Attribute"
        verbose_name_plural = "Product Attributes"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().title()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=100, help_text="Attribute value (e.g., 'Red', 'Large')")
    color_code = models.CharField(max_length=7, null=True, blank=True, help_text="Hex color for color attributes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['value']
        indexes = [
            models.Index(fields=['attribute'])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['attribute', 'value'],
                name="unique_value_per_attribute"
            )
        ]
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
    
    def save(self, *args, **kwargs):
        if self.value:
            self.value = self.value.strip().title()
        super().save(*args, **kwargs)
    



class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="product_reviews")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="product_reviews")
    rating = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Star rating (1-5)")
    title = models.CharField(max_length=255, null=True, blank=True, help_text="Review title")
    comment = models.TextField(null=True, blank=True, help_text="Review text")
    is_verified_purchase = models.BooleanField(default=False, help_text="Verified buyer flag")
    is_approved = models.BooleanField(default=False, help_text="Moderation status")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Helpful votes")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Review submission time")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last edit time")

    class Meta:
        db_table = "product_reviews"
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['order_item'],
                name="one_review_per_order_item"
            )
        ]

    def clean(self):
        if self.order_item.product_id != self.product_id:
            raise ValidationError("Order item does not match product.")
        
        if self.order_item.order.user_id != self.user_id:
            raise ValidationError("You can only review your own purchases.")
        
        if not self.title and not self.comment:
            raise ValidationError("Review must contain a title or comment")
        
    def save(self, *args, **kwargs):
        if self.order_item:
            self.is_verified_purchase = bool(self.order_item_id)
        self.full_clean()
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlists", help_text="Wishlist owner")
    name = models.CharField(max_length=200, help_text="Wishlist name")
    is_public = models.BooleanField(default=False, help_text="Public visibility")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")

    class Meta:
        db_table = "wishlists"
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name="unique_wishlist_name_per_user"
            )
        ]
    
    def save(self, *args, **kwargs):
        if self.name:
            base_name = self.name.strip().title()
        else:
            base_name = "My Wishlist"
        
        name = base_name
        counter = 1

        while Wishlist.objects.filter(user=self.user, name=name).exclude(pk=self.pk).exists():
            name = f"{base_name} ({counter})"
            counter += 1
        
        self.name = name
        super().save(*args, **kwargs)


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items", help_text="Parent wishlist")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="wishlist_entries", help_text="Saved product")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="wishlist_variant_entries", help_text="Specific variant")
    notes = models.TextField(null=True, blank=True, help_text="User notes")
    added_at = models.DateTimeField(auto_now_add=True, help_text="When item was added")

    class Meta:
        db_table = "wishlist_items"
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['wishlist']),
            models.Index(fields=['product']),
            models.Index(fields=['variant']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['wishlist', 'variant'],
                condition=Q(variant__isnull=False),
                name="unique_variant_per_wishlist"
            ),
            models.UniqueConstraint(
                fields=['wishlist', 'product'],
                condition=Q(variant__isnull=True),
                name="unique_product_per_wishlist"
            )
        ]
    
    def clean(self):
        if not self.product.is_active:
            raise ValidationError("Cannot add inactive products to the wishlist.")
        if self.variant and self.variant.product_id != self.product_id:
            raise ValidationError("Variant does not belong to the selected product.")
    
    def __str__(self):
        return str(self.variant or self.product)
    
    def save(self, *args, **kwargs):
        if self.notes:
            self.notes = self.notes.strip()
        self.full_clean()
        super().save(*args, **kwargs)