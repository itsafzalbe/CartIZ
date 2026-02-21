from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from stores.models import Market
from django.utils.text import slugify
from django.db.models import Q


# CATEGORY
# PRODUCT
# PRODUCT_IMAGE
# PRODUCT_VARIANT
# PRODUCT_ATTRIBUTE
# PRODUCT_ATTRIBUTE_VALUE


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
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
            models.Index(fields=['market']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active'])
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
    



