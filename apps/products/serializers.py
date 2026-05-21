"""
products/serializers.py
========================
Categories          (8)
Products            (17)
Product Stock       (3)
Product Images      (7)
Product Variants    (6)
Product Attributes  (8)
Product Reviews     (9)
Wishlist            (7)
Wishlist Items      (6)
Product Discovery   (8)
Product Browsing    (7)
Product Filtering   (12)
Personalization     (6)
Product Comparison  (3)
"""

from decimal import Decimal
from django.db.models import Avg, Count, Q, Min, Max
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User
from .models import *

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────
def _primary_image(product: Product) -> str | None:
    img = product.product_images.filter(is_primary=True).first()
    if not img:
        img = product.product_images.first()
    return img.image_url if img else None


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ═════════════════════════════════════════════════════════════════════════════

class CategorySerializer(serializers.ModelSerializer):
    """Basic category info - used as nested referenece """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active', 'order_position']
        read_only_fields = fields


class CategoryCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new category. Admin only
    POST /products/categories/
    """
    class Meta:
        model = Category
        fields = ['parent_id', 'name', 'description', 'image', 'icon', 'order_position', 'is_active']
        extra_kwargs = {"name": {"required": True}}
    
    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A cateogry with this name already exists.")
        return value

class CategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Updates category details. Admin only
    PATCH /products/categories/<id>/
    """

    class Meta:
        model = Category
        fields = ['parent_id', 'name', 'description', 'image', 'icon', 'order_position', 'is_active']
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class CategoryDeleteSerializer(serializers.Serializer):
    """
    Soft deletes a category by deactivating it.
    DELETE /products/categories/<id>/
    """

    def save(self):
        category        = self.context['category']
        category.is_active = False
        category.save(update_fields=['is_active'])


class CategoryListSerializer(serializers.ModelSerializer):
    """Minimal category data for list views and dropdowns"""

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'is_active', 'product_count']
        read_only_fields = fields

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Recursive category tree - used for mega menu and navigation
    GET /products/categories/tree/
    """

    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'order_position', 'children']
        read_only_fields = fields
    
    def get_children(self, obj):
        qs = obj.Children.filter(is_active=True).order_by('order_position')
        return CategoryTreeSerializer(qs, many=True).data

class CategoryDetailSerializer(serializers.ModelSerializer):
    """
    Category with subcategories and top products
    GET /products/categories/<id>/
    """

    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 
            'is_active', 'order_position', 'product_count', 
            'children',
        ]
        read_only_fields = fields
    
    def get_children(self, obj):
        qs = obj.Children.filter(is_active=True).order_by('order_position')
        return CategoryListSerializer(qs, many=True).data
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()



class CategoryProductCountSerializer(serializers.ModelSerializer):
    """Category with product count - used in the filter sidebars"""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count']
        read_only_fields = fields

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()



# ═════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═════════════════════════════════════════════════════════════════════════════

class ProductSerializer(serializers.ModelSerializer):
    """Basic product info - base / nested reference serializer"""
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
        'id', 'name', 'slug', 'sku', 
        'price', 'compare_at_price', 'discount_percentage', 
        'stock_quantity', 'in_stock', 'rating_average', 
        'review_count', 'is_active', 'is_featured', 'primary_image',
        'created_at',
        ]
        read_only_fields = fields
    
    def get_primary_image(self, obj):
        return _primary_image(obj)

class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new product for the authenticated seller's market
    POST /products/
    """

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'short_description', 
            'sku', 'barcode', 'price', 'compare_at_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold', 'weight', 'dimensions',
            'is_featured', 'is_active', 'is_digital',
        ]
        extra_kwargs = {
            'name':         {'required': True},
            'sku':          {'required': True},
            'barcode':      {'required': True},
            'price':        {'required': True},
            'cost_price':   {'required': True},
            'category':     {'required': True},
        }
    
    def validate(self, attrs):
        request = self.context['request']
        market = request.user.markets.filter(is_active=True).first()
        if not market:
            raise serializers.ValidationError("You must have an active market to create products.")
        self._market = market

        sku = attrs.get('sku', '')
        if Product.objects.filter(market=market, sku=sku).exists():
            raise serializers.ValidationError({"sku": "A product with this SKU already exists in your market."})

        barcode = attrs.get('barcode'. '')
        if Product.objects.filter(market=market, barcode=barcode).exists():
            raise serializers.ValidationError({"barcode": "A product with this barcode already exists in your market."})
            
        return attrs
    
    def create(self, validated_data):
        return Product.objects.create(market=self._market, **validated_data)


class ProductUpdateSerializer(serializers.ModelSerializer):
    """
    Updates product details. Seller only 
    PATCH /products/<id>/
    """

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'short_description', 
            'price', 'compare_at_price', 'cost_price', 
            'low_stock_threshold', 'weight', 'dimensions', 
            'is_featured', 'is_active', 'is_digital',
        ]
        extra_kwargs = {f: {'required': False} for f in fields}
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ProductDeleteSerializer(serializers.Serializer):
    """
    Soft-deletes (deactivates) a product
    DELETE /products/<id>/
    """

    def save(self):
        product             = self.context['product']
        product.is_active   = False
        product.save(update_fields=['is_active'])

class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Complete product page - images, variants, attributes, seller info.
    GET /products/<slug>/
    """
    images              = serializers.SerializerMethodField()
    variants            = serializers.SerializerMethodField()
    category            = CategorySerializer(read_only=True)
    market_name         = serializers.CharField(source='market.market_name', read_only=True)
    market_slug         = serializers.CharField(source='market.slug', read_only=True)
    market_verified     = serializers.BooleanField(source='market.is_verified', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()
    is_low_stock        = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'decription', 'short_description', 
            'sku', 'barcode', 'price', 'compare_at_price', 'cost_price', 
            'discount_percentage', 'stock_quantity', 'in_stock', 
            'is_low_stock', 'weight', 'dimensions', 'is_featured', 'is_active', 'is_digital',
            'rating_average', 'review_count', 'view_count', 'sold_count', 'category', 'market_name',
            'market_slug', 'market_verified', 'images', 'variants', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_images(self, obj):
        return ProductImageSerializer(
            obj.product_images,order_by('order_position'), many=True
        ).data
    
    def get_variants(self, obj):
        return ProductVariantSerializer(
            obj.product_variants.filter(is_active=True), many=True
        ).data












# ═════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═════════════════════════════════════════════════════════════════════════════

class ProductListSerializer(serializers.ModelSerializer):
    """
    Minimal product data optimised for listing pages.
    GET /products/
    """
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_at_price',
            'discount_percentage', 'in_stock',
            'rating_average', 'review_count',
            'primary_image', 'is_featured',
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductCardSerializer(serializers.ModelSerializer):
    """Product card for grid / list views."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()
    market_name         = serializers.CharField(source='market.market_name', read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug',
            'price', 'compare_at_price', 'discount_percentage',
            'rating_average', 'review_count',
            'in_stock', 'is_featured',
            'primary_image', 'market_name',
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductSearchSerializer(serializers.ModelSerializer):
    """Search result item — minimal data for fast rendering."""
    primary_image = serializers.SerializerMethodField()
    in_stock      = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image', 'in_stock']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductSellerSerializer(serializers.ModelSerializer):
    """
    Product from the seller's management dashboard — includes cost and stock.
    GET /products/my-products/
    """
    primary_image = serializers.SerializerMethodField()
    is_low_stock  = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'barcode',
            'price', 'cost_price', 'compare_at_price',
            'stock_quantity', 'is_low_stock',
            'rating_average', 'review_count',
            'sold_count', 'view_count',
            'is_active', 'is_featured',
            'primary_image', 'created_at',
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductPublicSerializer(serializers.ModelSerializer):
    """Product as buyers see it — no cost_price."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()
    category_name       = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'price', 'compare_at_price', 'discount_percentage',
            'stock_quantity', 'in_stock',
            'rating_average', 'review_count', 'sold_count',
            'is_digital', 'category_name',
            'primary_image',
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductQuickViewSerializer(serializers.ModelSerializer):
    """Quick view modal — limited data loaded on hover/click."""
    primary_image       = serializers.SerializerMethodField()
    variants            = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'short_description',
            'price', 'compare_at_price', 'discount_percentage',
            'in_stock', 'rating_average', 'review_count',
            'primary_image', 'variants',
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)

    def get_variants(self, obj):
        return ProductVariantListSerializer(
            obj.product_variants.filter(is_active=True), many=True
        ).data


class ProductRelatedSerializer(serializers.ModelSerializer):
    """Related / similar products — same category, different product."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductStatsSerializer(serializers.Serializer):
    """
    Product performance stats for the seller dashboard.
    GET /products/<id>/stats/
    """

    def to_representation(self, instance: Product):
        return {
            'view_count':    instance.view_count,
            'sold_count':    instance.sold_count,
            'review_count':  instance.review_count,
            'rating_average': str(instance.rating_average),
            'stock_quantity': instance.stock_quantity,
            'is_low_stock':   instance.is_low_stock,
            'in_stock':       instance.in_stock,
        }


class ProductFeaturedSerializer(serializers.ModelSerializer):
    """Featured products for the homepage."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_at_price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductBestSellerSerializer(serializers.ModelSerializer):
    """Best-selling products sorted by sold_count."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'sold_count', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductNewArrivalSerializer(serializers.ModelSerializer):
    """Newly added products."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image', 'created_at']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductTrendingSerializer(serializers.ModelSerializer):
    """Trending products sorted by view_count."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'view_count', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ProductTopRatedSerializer(serializers.ModelSerializer):
    """Highest-rated products."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'review_count', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT STOCK
# ═════════════════════════════════════════════════════════════════════════════

class ProductStockSerializer(serializers.ModelSerializer):
    """Current stock info for a product."""
    is_low_stock = serializers.ReadOnlyField()
    in_stock     = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'sku', 'stock_quantity', 'low_stock_threshold', 'is_low_stock', 'in_stock']
        read_only_fields = fields


class ProductStockUpdateSerializer(serializers.ModelSerializer):
    """
    Updates product quantity. Seller only.
    PATCH /products/<id>/stock/
    """

    class Meta:
        model  = Product
        fields = ['stock_quantity', 'low_stock_threshold']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data.keys()))
        return instance


class ProductLowStockSerializer(serializers.ModelSerializer):
    """Products below their low_stock_threshold."""
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'sku', 'stock_quantity', 'low_stock_threshold', 'is_low_stock']
        read_only_fields = fields


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT IMAGES
# ═════════════════════════════════════════════════════════════════════════════

class ProductImageSerializer(serializers.ModelSerializer):
    """Full image detail."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = ProductImage
        fields = ['id', 'image_url', 'alt_text', 'is_primary', 'order_position', 'created_at']
        read_only_fields = fields

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class ProductImageCreateSerializer(serializers.ModelSerializer):
    """
    Uploads a new product image.
    POST /products/<id>/images/
    """

    class Meta:
        model  = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order_position']

    def validate(self, attrs):
        product = self.context['product']
        if attrs.get('is_primary'):
            # Will be handled atomically in create
            pass
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        product    = self.context['product']
        is_primary = validated_data.get('is_primary', False)

        with transaction.atomic():
            if is_primary:
                ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
            return ProductImage.objects.create(product=product, **validated_data)


class ProductImageUpdateSerializer(serializers.ModelSerializer):
    """
    Updates alt_text, order_position.
    PATCH /products/images/<id>/
    """

    class Meta:
        model  = ProductImage
        fields = ['alt_text', 'order_position']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductImageDeleteSerializer(serializers.Serializer):
    """Deletes a product image. Cannot delete the only image."""

    def validate(self, attrs):
        image   = self.context['image']
        product = image.product
        if product.product_images.count() <= 1:
            raise serializers.ValidationError("Cannot delete the only product image.")
        return attrs

    def save(self):
        image = self.context['image']
        image.image.delete(save=False)
        image.delete()


class ProductImageListSerializer(serializers.ModelSerializer):
    """All images for a product."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = ProductImage
        fields = ['id', 'image_url', 'alt_text', 'is_primary', 'order_position']
        read_only_fields = fields

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class SetPrimaryImageSerializer(serializers.Serializer):
    """
    Sets a product image as primary.
    PATCH /products/images/<id>/set-primary/
    """

    def save(self):
        from django.db import transaction
        image   = self.context['image']
        product = image.product
        with transaction.atomic():
            ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
            image.is_primary = True
            image.save(update_fields=['is_primary'])


class ProductImageBulkUploadSerializer(serializers.Serializer):
    """
    Bulk upload multiple images for a product.
    POST /products/<id>/images/bulk/
    """
    images = serializers.ListField(child=serializers.ImageField(), min_length=1, max_length=10)

    def save(self):
        from django.db import transaction
        product = self.context['product']
        created = []
        with transaction.atomic():
            for i, img in enumerate(self.validated_data['images']):
                created.append(ProductImage.objects.create(
                    product=product,
                    image=img,
                    order_position=i,
                ))
        return created


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT VARIANTS
# ═════════════════════════════════════════════════════════════════════════════

class ProductVariantSerializer(serializers.ModelSerializer):
    """Full variant details."""
    in_stock      = serializers.ReadOnlyField()
    low_in_stock  = serializers.ReadOnlyField()
    image_url     = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = [
            'id', 'variant_name', 'sku', 'price',
            'stock_quantity', 'in_stock', 'low_in_stock',
            'attributes', 'image_url', 'is_active',
            'created_at',
        ]
        read_only_fields = fields

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class ProductVariantCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new product variant. Seller only.
    POST /products/<id>/variants/
    """

    class Meta:
        model  = ProductVariant
        fields = ['variant_name', 'sku', 'price', 'stock_quantity', 'attributes', 'image', 'is_active']
        extra_kwargs = {
            'variant_name': {'required': True},
            'sku':          {'required': True},
            'price':        {'required': True},
        }

    def validate_sku(self, value):
        product = self.context['product']
        if ProductVariant.objects.filter(product=product, sku=value).exists():
            raise serializers.ValidationError("A variant with this SKU already exists for this product.")
        return value

    def create(self, validated_data):
        return ProductVariant.objects.create(product=self.context['product'], **validated_data)


class ProductVariantUpdateSerializer(serializers.ModelSerializer):
    """
    Updates variant details. Seller only.
    PATCH /products/variants/<id>/
    """

    class Meta:
        model  = ProductVariant
        fields = ['variant_name', 'price', 'stock_quantity', 'attributes', 'image', 'is_active']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductVariantDeleteSerializer(serializers.Serializer):
    """Deactivates a variant."""

    def save(self):
        variant           = self.context['variant']
        variant.is_active = False
        variant.save(update_fields=['is_active'])


class ProductVariantListSerializer(serializers.ModelSerializer):
    """Lightweight variant list — price, stock, attributes."""
    in_stock  = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = ['id', 'variant_name', 'sku', 'price', 'stock_quantity', 'in_stock', 'attributes', 'image_url']
        read_only_fields = fields

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class ProductVariantStockSerializer(serializers.ModelSerializer):
    """Variant stock info for inventory management."""
    in_stock     = serializers.ReadOnlyField()
    low_in_stock = serializers.ReadOnlyField()

    class Meta:
        model  = ProductVariant
        fields = ['id', 'variant_name', 'sku', 'stock_quantity', 'in_stock', 'low_in_stock']
        read_only_fields = fields


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT ATTRIBUTES
# ═════════════════════════════════════════════════════════════════════════════

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """Single attribute value (e.g. 'Red', 'Large')."""

    class Meta:
        model  = ProductAttributeValue
        fields = ['id', 'value', 'color_code']
        read_only_fields = fields


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Attribute with its values."""
    values = ProductAttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model  = ProductAttribute
        fields = ['id', 'name', 'slug', 'values']
        read_only_fields = fields


class ProductAttributeCreateSerializer(serializers.ModelSerializer):
    """Creates a new attribute type. Admin only."""

    class Meta:
        model  = ProductAttribute
        fields = ['name']
        extra_kwargs = {'name': {'required': True}}

    def validate_name(self, value):
        if ProductAttribute.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("This attribute already exists.")
        return value


class ProductAttributeUpdateSerializer(serializers.ModelSerializer):
    """Updates attribute name. Admin only."""

    class Meta:
        model  = ProductAttribute
        fields = ['name']

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


class ProductAttributeDeleteSerializer(serializers.Serializer):
    """Deletes an attribute and all its values."""

    def save(self):
        self.context['attribute'].delete()


class ProductAttributeListSerializer(serializers.ModelSerializer):
    """All attributes — used in filter sidebar."""
    value_count = serializers.SerializerMethodField()

    class Meta:
        model  = ProductAttribute
        fields = ['id', 'name', 'slug', 'value_count']
        read_only_fields = fields

    def get_value_count(self, obj):
        return obj.values.count()


class ProductAttributeValueCreateSerializer(serializers.ModelSerializer):
    """Adds a new value to an attribute."""

    class Meta:
        model  = ProductAttributeValue
        fields = ['value', 'color_code']
        extra_kwargs = {'value': {'required': True}}

    def validate_value(self, value):
        attribute = self.context['attribute']
        if ProductAttributeValue.objects.filter(attribute=attribute, value__iexact=value).exists():
            raise serializers.ValidationError("This value already exists for this attribute.")
        return value

    def create(self, validated_data):
        return ProductAttributeValue.objects.create(
            attribute=self.context['attribute'], **validated_data
        )


class ProductAttributeValueListSerializer(serializers.ModelSerializer):
    """All values for a given attribute."""

    class Meta:
        model  = ProductAttributeValue
        fields = ['id', 'value', 'color_code']
        read_only_fields = fields


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT REVIEWS
# ═════════════════════════════════════════════════════════════════════════════

class ProductReviewSerializer(serializers.ModelSerializer):
    """Full review details."""
    reviewer_name   = serializers.SerializerMethodField()
    reviewer_avatar = serializers.SerializerMethodField()

    class Meta:
        model  = ProductReview
        fields = [
            'id', 'reviewer_name', 'reviewer_avatar',
            'rating', 'title', 'comment',
            'is_verified_purchase', 'is_approved',
            'helpful_count', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_reviewer_avatar(self, obj):
        return obj.user.get_avatar_url()


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    """
    Creates a review — requires a verified purchase (order_item).
    POST /products/<id>/reviews/
    """

    class Meta:
        model  = ProductReview
        fields = ['order_item', 'rating', 'title', 'comment']
        extra_kwargs = {
            'order_item': {'required': True},
            'rating':     {'required': True},
        }

    def validate(self, attrs):
        user       = self.context['request'].user
        product    = self.context['product']
        order_item = attrs['order_item']

        if order_item.product_id != product.pk:
            raise serializers.ValidationError({"order_item": "This order item does not match the product."})
        if order_item.order.user_id != user.pk:
            raise serializers.ValidationError({"order_item": "You can only review your own purchases."})
        if ProductReview.objects.filter(order_item=order_item).exists():
            raise serializers.ValidationError("You have already reviewed this purchase.")

        return attrs

    def create(self, validated_data):
        return ProductReview.objects.create(
            product=self.context['product'],
            user=self.context['request'].user,
            **validated_data,
        )


class ProductReviewUpdateSerializer(serializers.ModelSerializer):
    """Edits own review."""

    class Meta:
        model  = ProductReview
        fields = ['rating', 'title', 'comment']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductReviewDeleteSerializer(serializers.Serializer):
    """Validates ownership before deletion."""

    def validate(self, attrs):
        review = self.context['review']
        user   = self.context['request'].user
        if review.user_id != user.pk and not user.is_staff:
            raise serializers.ValidationError("You can only delete your own reviews.")
        return attrs

    def save(self):
        self.context['review'].delete()


class ProductReviewListSerializer(serializers.ModelSerializer):
    """Lightweight review list item."""
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model  = ProductReview
        fields = ['id', 'reviewer_name', 'rating', 'title', 'comment', 'is_verified_purchase', 'created_at']
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class ProductReviewStatsSerializer(serializers.Serializer):
    """Rating breakdown — 1 to 5 star distribution."""

    def to_representation(self, instance: Product):
        approved  = instance.reviews.filter(is_approved=True)
        avg       = approved.aggregate(avg=Avg('rating'))['avg'] or 0
        breakdown = {str(i): 0 for i in range(1, 6)}
        for row in approved.values('rating').annotate(count=Count('id')):
            breakdown[str(int(row['rating']))] = row['count']
        return {
            'total_reviews':    approved.count(),
            'average_rating':   round(float(avg), 2),
            'rating_breakdown': breakdown,
        }


class ProductReviewHelpfulSerializer(serializers.Serializer):
    """
    Increments helpful_count on a review.
    POST /products/reviews/<id>/helpful/
    """

    def save(self):
        review               = self.context['review']
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])


class ProductReviewVerifiedSerializer(serializers.ModelSerializer):
    """Verified purchase reviews only."""
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model  = ProductReview
        fields = ['id', 'reviewer_name', 'rating', 'title', 'comment', 'helpful_count', 'created_at']
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class ProductReviewWithImagesSerializer(serializers.ModelSerializer):
    """Reviews that have attached customer photos (placeholder — add ReviewImage model when ready)."""
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model  = ProductReview
        fields = ['id', 'reviewer_name', 'rating', 'title', 'comment', 'created_at']
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


# ═════════════════════════════════════════════════════════════════════════════
# WISHLIST
# ═════════════════════════════════════════════════════════════════════════════

class WishlistSerializer(serializers.ModelSerializer):
    """Basic wishlist info."""
    item_count = serializers.SerializerMethodField()

    class Meta:
        model  = Wishlist
        fields = ['id', 'name', 'is_public', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'item_count', 'created_at', 'updated_at']

    def get_item_count(self, obj):
        return obj.items.count()


class WishlistCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new wishlist.
    POST /products/wishlists/
    """

    class Meta:
        model  = Wishlist
        fields = ['name', 'is_public']
        extra_kwargs = {'name': {'required': True}}

    def create(self, validated_data):
        return Wishlist.objects.create(user=self.context['request'].user, **validated_data)


class WishlistUpdateSerializer(serializers.ModelSerializer):
    """Updates wishlist name/visibility."""

    class Meta:
        model  = Wishlist
        fields = ['name', 'is_public']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class WishlistDeleteSerializer(serializers.Serializer):
    """Deletes a wishlist and all its items."""

    def validate(self, attrs):
        wishlist = self.context['wishlist']
        if wishlist.user_id != self.context['request'].user.pk:
            raise serializers.ValidationError("You can only delete your own wishlists.")
        return attrs

    def save(self):
        self.context['wishlist'].delete()


class WishlistListSerializer(serializers.ModelSerializer):
    """All user wishlists — minimal data."""
    item_count = serializers.SerializerMethodField()

    class Meta:
        model  = Wishlist
        fields = ['id', 'name', 'is_public', 'item_count', 'updated_at']
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.items.count()


class WishlistItemCountSerializer(serializers.Serializer):
    """Total items across all user wishlists — for badge display."""

    def to_representation(self, instance: User):
        total = WishlistItem.objects.filter(wishlist__user=instance).count()
        return {'total_items': total}


class WishlistDetailSerializer(serializers.ModelSerializer):
    """Wishlist with all items fully hydrated."""
    items      = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model  = Wishlist
        fields = ['id', 'name', 'is_public', 'item_count', 'items', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_items(self, obj):
        return WishlistItemDetailSerializer(obj.items.all(), many=True).data

    def get_item_count(self, obj):
        return obj.items.count()


# ═════════════════════════════════════════════════════════════════════════════
# WISHLIST ITEMS
# ═════════════════════════════════════════════════════════════════════════════

class WishlistItemSerializer(serializers.ModelSerializer):
    """Single wishlist item details."""
    product_name  = serializers.CharField(source='product.name', read_only=True)
    product_slug  = serializers.CharField(source='product.slug', read_only=True)
    variant_name  = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = WishlistItem
        fields = ['id', 'product_name', 'product_slug', 'variant_name', 'primary_image', 'notes', 'added_at']
        read_only_fields = fields

    def get_variant_name(self, obj):
        return obj.variant.variant_name if obj.variant else None

    def get_primary_image(self, obj):
        return _primary_image(obj.product)


class WishlistItemCreateSerializer(serializers.ModelSerializer):
    """
    Adds a product/variant to a wishlist.
    POST /products/wishlists/<id>/items/
    """

    class Meta:
        model  = WishlistItem
        fields = ['product', 'variant', 'notes']
        extra_kwargs = {'product': {'required': True}}

    def validate(self, attrs):
        wishlist = self.context['wishlist']
        product  = attrs['product']
        variant  = attrs.get('variant')

        if not product.is_active:
            raise serializers.ValidationError({"product": "This product is no longer available."})

        if variant and variant.product_id != product.pk:
            raise serializers.ValidationError({"variant": "Variant does not belong to this product."})

        # Check duplicate
        if variant:
            if wishlist.items.filter(variant=variant).exists():
                raise serializers.ValidationError("This variant is already in the wishlist.")
        else:
            if wishlist.items.filter(product=product, variant__isnull=True).exists():
                raise serializers.ValidationError("This product is already in the wishlist.")

        return attrs

    def create(self, validated_data):
        return WishlistItem.objects.create(wishlist=self.context['wishlist'], **validated_data)


class WishlistItemDeleteSerializer(serializers.Serializer):
    """Removes a single item from a wishlist."""

    def save(self):
        self.context['item'].delete()


class WishlistItemListSerializer(serializers.ModelSerializer):
    """Minimal wishlist item list — product name, image, price."""
    product_name  = serializers.CharField(source='product.name',  read_only=True)
    product_slug  = serializers.CharField(source='product.slug',  read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = WishlistItem
        fields = ['id', 'product_name', 'product_slug', 'product_price', 'primary_image', 'added_at']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj.product)


class WishlistItemDetailSerializer(serializers.ModelSerializer):
    """Wishlist item with full product and variant details."""
    product = ProductCardSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model  = WishlistItem
        fields = ['id', 'product', 'variant', 'notes', 'added_at']
        read_only_fields = fields


class WishlistItemBulkDeleteSerializer(serializers.Serializer):
    """
    Removes multiple items from a wishlist.
    DELETE /products/wishlists/<id>/items/bulk/
    """
    item_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)

    def validate_item_ids(self, value):
        wishlist = self.context['wishlist']
        existing = set(wishlist.items.filter(pk__in=value).values_list('pk', flat=True))
        invalid  = set(value) - existing
        if invalid:
            raise serializers.ValidationError(f"Items not found in this wishlist: {list(invalid)}")
        return value

    def save(self):
        wishlist = self.context['wishlist']
        wishlist.items.filter(pk__in=self.validated_data['item_ids']).delete()


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT DISCOVERY
# ═════════════════════════════════════════════════════════════════════════════

class FeaturedProductsSerializer(serializers.ModelSerializer):
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_at_price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class TrendingProductsSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'view_count', 'sold_count', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class NewArrivalsSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image', 'created_at']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class BestSellersSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'sold_count', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class SimilarProductsSerializer(serializers.ModelSerializer):
    """Same category, same market — exclude the current product."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class FrequentlyBoughtTogetherSerializer(serializers.ModelSerializer):
    """Products often ordered together — placeholder until analytics data exists."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class YouMayAlsoLikeSerializer(serializers.ModelSerializer):
    """Personalised recommendations — same category, high rating."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class RecommendedProductsSerializer(serializers.ModelSerializer):
    """Recommendations based on user browse history — same as YouMayAlsoLike shape."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT BROWSING
# ═════════════════════════════════════════════════════════════════════════════

class CategoryBrowseSerializer(serializers.ModelSerializer):
    """Category page — subcategories + product count."""
    children      = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'product_count', 'children']
        read_only_fields = fields

    def get_children(self, obj):
        return CategoryListSerializer(obj.Children.filter(is_active=True), many=True).data

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryProductListSerializer(serializers.ModelSerializer):
    """Products in a category — same as ProductListSerializer, filter applied in view."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_at_price', 'discount_percentage', 'in_stock', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class SubcategoryListSerializer(serializers.ModelSerializer):
    """Subcategories of a given category."""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'product_count']
        read_only_fields = fields

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryBreadcrumbSerializer(serializers.Serializer):
    """
    Navigation breadcrumb trail for a product/category page.
    Walks parent_id chain upward.
    """

    def to_representation(self, instance: Category):
        breadcrumb = []
        current    = instance
        while current:
            breadcrumb.insert(0, {'id': current.pk, 'name': current.name, 'slug': current.slug})
            current = current.parent_id
        return {'breadcrumb': breadcrumb}


class PopularCategoriesSerializer(serializers.ModelSerializer):
    """Most popular categories by product count."""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'product_count']
        read_only_fields = fields

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryWithTopProductsSerializer(serializers.ModelSerializer):
    """Category with its top 4 rated products."""
    top_products = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'top_products']
        read_only_fields = fields

    def get_top_products(self, obj):
        qs = obj.products.filter(is_active=True).order_by('-rating_average')[:4]
        return ProductCardSerializer(qs, many=True).data


class ProductListPageSerializer(serializers.Serializer):
    """
    Aggregated data for a complete product listing page:
    products + available filters + price range.
    Assembled in the view.
    """
    products      = ProductListSerializer(many=True)
    total_count   = serializers.IntegerField()
    price_min     = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_max     = serializers.DecimalField(max_digits=10, decimal_places=2)
    categories    = CategoryProductCountSerializer(many=True)


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT FILTERING
# ═════════════════════════════════════════════════════════════════════════════

class ProductFilterSerializer(serializers.Serializer):
    """Input serializer — validates filter params from query string."""
    q             = serializers.CharField(required=False, allow_blank=True)
    category      = serializers.IntegerField(required=False)
    min_price     = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    max_price     = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    min_rating    = serializers.DecimalField(required=False, max_digits=3, decimal_places=2)
    in_stock      = serializers.BooleanField(required=False)
    is_featured   = serializers.BooleanField(required=False)
    market        = serializers.IntegerField(required=False)
    sort          = serializers.ChoiceField(
        required=False,
        choices=['price_asc', 'price_desc', 'rating', 'newest', 'popular', 'sales'],
    )


class PriceRangeFilterSerializer(serializers.Serializer):
    """Filter by price range."""
    min_price = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    max_price = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)

    def validate(self, attrs):
        if attrs['min_price'] > attrs['max_price']:
            raise serializers.ValidationError("min_price cannot be greater than max_price.")
        return attrs


class RatingFilterSerializer(serializers.Serializer):
    """Filter by minimum rating."""
    min_rating = serializers.DecimalField(
        required=True, max_digits=3, decimal_places=2,
        min_value=Decimal('1'), max_value=Decimal('5'),
    )


class BrandFilterSerializer(serializers.Serializer):
    """Filter by market/brand IDs."""
    market_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class AvailabilityFilterSerializer(serializers.Serializer):
    """Filter in-stock / out-of-stock."""
    in_stock = serializers.BooleanField(required=True)


class AttributeFilterSerializer(serializers.Serializer):
    """Filter by attribute value IDs (e.g. colour=Red, size=Large)."""
    attribute_value_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class SortOptionsSerializer(serializers.Serializer):
    """Available sorting options returned to the frontend."""

    def to_representation(self, instance):
        return {
            'options': [
                {'value': 'newest',     'label': 'Newest First'},
                {'value': 'price_asc',  'label': 'Price: Low to High'},
                {'value': 'price_desc', 'label': 'Price: High to Low'},
                {'value': 'rating',     'label': 'Highest Rated'},
                {'value': 'popular',    'label': 'Most Viewed'},
                {'value': 'sales',      'label': 'Best Selling'},
            ]
        }


class AvailableFiltersSerializer(serializers.Serializer):
    """All available filters for a result set — assembled in the view."""

    def to_representation(self, instance):
        qs         = instance
        price_data = qs.aggregate(min=Min('price'), max=Max('price'))
        categories = Category.objects.filter(
            products__in=qs
        ).annotate(count=Count('products')).order_by('-count')[:10]

        return {
            'price_range': {
                'min': str(price_data['min'] or 0),
                'max': str(price_data['max'] or 0),
            },
            'categories': CategoryProductCountSerializer(categories, many=True).data,
            'in_stock_count': qs.filter(stock_quantity__gt=0).count(),
        }


class ActiveFiltersSerializer(serializers.Serializer):
    """Currently applied filters — for the active-filter chips UI."""
    filters = serializers.DictField(child=serializers.CharField())


class FilterCountSerializer(serializers.Serializer):
    """Product count per filter option."""
    filter_type  = serializers.CharField()
    filter_value = serializers.CharField()
    count        = serializers.IntegerField()


class PriceRangeSerializer(serializers.Serializer):
    """Min/max price for the current result set."""

    def to_representation(self, qs):
        data = qs.aggregate(min=Min('price'), max=Max('price'))
        return {
            'min': str(data['min'] or 0),
            'max': str(data['max'] or 0),
        }


class ProductGridSerializer(serializers.ModelSerializer):
    """Products formatted for grid view — same as ProductCardSerializer."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_at_price', 'discount_percentage', 'in_stock', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


# ═════════════════════════════════════════════════════════════════════════════
# PERSONALIZATION
# ═════════════════════════════════════════════════════════════════════════════

class PersonalizedFeedSerializer(serializers.ModelSerializer):
    """Personalised product feed — top rated from categories user has browsed."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class RecentlyViewedSerializer(serializers.ModelSerializer):
    """
    User's recently viewed products.
    Requires a RecentlyViewed model / Redis cache — placeholder shape.
    """
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ViewHistorySerializer(serializers.ModelSerializer):
    """Complete browsing history shape (plug into RecentlyViewed model)."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class ForYouSerializer(serializers.ModelSerializer):
    """"For You" feed — high-rated products from user's top categories."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'discount_percentage', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class BasedOnYourInterestsSerializer(serializers.ModelSerializer):
    """Products matching user's wishlist categories."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


class BecauseYouViewedSerializer(serializers.ModelSerializer):
    """"Because you viewed X" — same category as a reference product."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'rating_average', 'primary_image']
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT COMPARISON
# ═════════════════════════════════════════════════════════════════════════════

class ProductCompareSerializer(serializers.ModelSerializer):
    """Full product data shaped for side-by-side comparison."""
    primary_image       = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock            = serializers.ReadOnlyField()
    category_name       = serializers.CharField(source='category.name', read_only=True)
    attributes          = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'category_name',
            'price', 'compare_at_price', 'discount_percentage',
            'stock_quantity', 'in_stock',
            'weight', 'dimensions',
            'rating_average', 'review_count', 'sold_count',
            'is_digital', 'primary_image', 'attributes',
        ]
        read_only_fields = fields

    def get_primary_image(self, obj):
        return _primary_image(obj)

    def get_attributes(self, obj):
        """Flatten variant attributes into a unified dict for comparison."""
        attrs = {}
        for variant in obj.product_variants.filter(is_active=True):
            if variant.attributes:
                attrs.update(variant.attributes)
        return attrs


class ProductCompareAddSerializer(serializers.Serializer):
    """
    Adds a product to the comparison list (client-side session / localStorage).
    POST /products/compare/add/
    Max 4 products in comparison at once.
    """
    product_id      = serializers.IntegerField()
    current_compare = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        try:
            self._product = Product.objects.get(pk=attrs['product_id'], is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found."})

        current = attrs.get('current_compare', [])
        if len(current) >= 4:
            raise serializers.ValidationError("You can compare at most 4 products at a time.")
        if attrs['product_id'] in current:
            raise serializers.ValidationError("This product is already in your comparison list.")
        return attrs

    def save(self):
        return self._product


class ProductCompareListSerializer(serializers.Serializer):
    """
    Returns full comparison data for a list of product IDs.
    POST /products/compare/
    """
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=2,
        max_length=4,
    )

    def validate_product_ids(self, value):
        products = Product.objects.filter(pk__in=value, is_active=True)
        if products.count() != len(value):
            raise serializers.ValidationError("One or more products were not found.")
        self._products = products
        return value

    def save(self):
        return ProductCompareSerializer(self._products, many=True).data