from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Product
from .models import Coupon, CouponUsage, FlashSale, Promotion


#shared helpers
def _primary_image(product: Product) -> str | None:
    img = product.product_images.filter(is_primary=True).first() or product.product_images.first()
    return img.image.url if img else None



#COUPONS 
class CouponSerializer(serializers.ModelSerializer):
    """Basic coupon detail - used as a nested reference."""
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    is_currently_active = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    uses_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description',
            'discount_type', 'discount_type_display', 'discount_value',
            'min_purchase_amount', 'max_discount_amount',
            'usage_limit', 'usage_count', 'uses_remaining',
            'per_user_limit',
            'valid_from', 'valid_until',
            'is_active', 'is_currently_active', 'is_expired',
            'created_at',
        ]
        read_only_fields = fields 


class CouponListSerializer(serializers.ModelSerializer):
    """Lightweight coupon row for list views."""
    is_currently_active = serializers.ReadOnlyField()
    uses_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'valid_from', 'valid_until',
            'is_active', 'is_currently_active',
            'usage_count', 'uses_remaining',
        ]
        read_only_fields = fields

class CouponDetailSerializer(serializers.ModelSerializer):
    """Complete coupon with market info and usage count."""
    market_name = serializers.CharField(source='market.market_name', read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    is_currently_active = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    uses_remaining = serializers.ReadOnlyField()
    usage_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'market_name', 'code', 'description',
            'discount_type', 'discount_type_display', 'discount_value',
            'min_purchase_amount', 'max_discount_amount',
            'usage_limit', 'usage_count', 'uses_remaining',
            'per_user_limit',
            'valid_from', 'valid_until',
            'is_active', 'is_currently_active', 'is_expired',
            'usage_breakdown', 'created_at',
        ]
        read_only_fields = fields
    
    def get_usage_breakdown(self, obj):
        agg = obj.usages.aggregate(
            total_uses=Count('id'),
            total_discount=Sum('discount_amount'),
        )
        return {
            'total_uses': agg['total_uses'] or 0,
            'total_discount': str(agg['total_discount'] or Decimal('0.00')),
        }

class CouponCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new coupon for the seller's market.
    POST /promotions/coupons/
    """
    class Meta:
        model = Coupon
        fields = [
            'code', 'description',
            'discount_type', 'discount_value',
            'min_purchase_amount', 'max_discount_amount',
            'usage_limit', 'per_user_limit',
            'valid_from', 'valid_until',
            'is_active',
        ]
        extra_kwargs = {
            'code':           {'required': True},
            'discount_type':  {'required': True},
            'discount_value': {'required': True},
            'valid_from':     {'required': True},
            'valid_until':    {'required': True},
        }
    
    def validate_code(self, value):
        if Coupon.objects.filter(code__iexact=value).exists():
            raise serializers.ValidationError("A coupon with this code already exists.")
        return value.upper()
    
    def validate(self, attrs):
        if attrs['valid_until'] <- attrs['valid_from']:
            raise serializers.ValidationError({'valid_until': 'Must be after valid_from.'})
        
        if attrs['discount_type'] == Coupon.PERCENTAGE and attrs['discount_value'] > 100:
            raise serializers.ValidationError({'discount_value': 'Percentage cannot exceed 100.'})
        
        market = self.context['request'].user.markets.filter(is_active=True).first()
        if not market:
            raise serializers.ValidationError("You must have an active market to create coupons.")
        self._market = market
        return attrs
    
    def create(self, validated_data):
        return Coupon.objects.create(market=self._market, **validated_data)


class CouponUpdateSerializer(serializers.ModelSerializer):
    """
    Updates coupon details. Seller only
    PATCH /promotions/coupons/<id>/
    Cannot change the code after creation.
    """
    class Meta:
        model = Coupon
        fields = [
            'description', 'discount_type', 'discount_value',
            'min_purchase_amount', 'max_discount_amount',
            'usage_limit', 'per_user_limit',
            'valid_from', 'valid_until', 'is_active',
        ]
        extra_kwargs = {f: {'required': False} for f in fields}
    
    def validate(self, attrs):
        vf = attrs.get('valid_from', self.instance.valid_from)
        vu = attrs.get('valid_until', self.instance.valid_until)
        if vu <= vf:
            raise serializers.ValidationError({'valid_until': 'Must be after valid_from.'})
        return attrs
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class CouponDeleteSerializer(serializers.Serializer):
    """Deactivates a coupon (soft-deletes)."""

    def save(self, **kwargs):
        coupon = self.context['coupon']
        coupon.is_active = False
        coupon.save(update_fields=['is_active'])


class CouponPublicSerializer(serializers.ModelSerializer):
    """
    Publicly visible coupon info - no internal stats,no per-user data.
    Used in market storefront/promotional banners.
    """

    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    is_currently_active = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description',
            'discount_type', 'discount_type_display', 'discount_value',
            'min_purchase_amount', 'max_discount_amount',
            'valid_until', 'is_currently_active',
        ]
        read_only_fields = fields

class CouponActiveSerializer(serializers.ModelSerializer):
    """Currently active coupons - used in storefront and cart page."""
    uses_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'min_purchase_amount', 'valid_until', 'uses_remaining',
        ]
        read_only_fields = fields
    

class CouponValidateSerializer(serializers.Serializer):
    """
    Validates a coupon code without applying it.
    POST /promotions/coupons/validate/
    Body:  { "code": "SAVE20", "cart_total": "99.99" }
    Returns discount amount if valid.
    """
    code = serializers.CharField(max_length=50)
    cart_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate(self, attrs):
        now = timezone.now()
        try:
            coupon = Coupon.objects.get(
                code__iexact=attrs['code'],
                is_active=True,
                valid_from__lte = now,
                valid_until__gte = now,
            )
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"code": "Invalid or expired coupon code"})
        
        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            raise serializers.ValidationError({"code": "This coupon has reached its usage limit."})
        
        user = self.context['request'].user
        user_usage = coupon.usages.filter(user=user).count()
        if user_usage >= coupon.per_user_limit:
            raise serializers.ValidationError({"code": "You have used this coupon the maximum number of times."})
        
        cart_total = attrs.get('cart_total')
        if cart_total and coupon.min_purchase_amount and cart_total < coupon.min_purchase_amount:
            raise serializers.ValidationError(
                {"code": f"Minimum purchase of {coupon.min_purchase_amount} required."}
            )
        attrs['_coupon'] = coupon
        return attrs
    
    def get_discount(self) -> dict:
        coupon = self.validated_data['_coupon']
        cart_total = self.validated_data.get('cart_total', Decimal('0.00'))

        if coupon.discount_type == Coupon.PERCENTAGE:
            discount = (cart_total * coupon.discount_value / 100).quantize(Decimal('0.01'))
        else:
            discount = coupon.discount_value
        
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
        
        return {
            'code':           coupon.code,
            'discount_type':  coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'discount_amount': str(discount),
            'valid_until':    coupon.valid_until,
        }

class CouponApplySerializer(serializers.Serializer):
    """
    Applies a coupon to the current cart session
    POST /promotions/coupons/apply/
    Body: { "code": "SAVE20" }
    Returns computed discount
    """
    code = serializers.CharField(max_length=50)

    def validate_code(self, value):
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(
                code__iexact=value,
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now,
            )
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired coupon code.")
        
        if coupon.usage_limit is not None and coupon.usage_count >- coupon.usage_limit:
            raise serializers.ValidationError("This coupon has reached its usage limit.")
        
        user = self.context['request'].user
        if coupon.usages.filter(user=user).count() >= coupon.per_user_limit:
            raise serializers.ValidationError("You have already used this coupon the maximum number of times.")
        
        self._coupon = coupon
        return value
    
    def get_coupon(self) -> Coupon:
        return self._coupon
    
    def compute_discount(self, cart_total: Decimal) -> Decimal:
        coupon = self._coupon
        if coupon.min_purchase_amount and cart_total < coupon.min_purchase_amount:
            raise serializers.ValidationError(
                f"Minimum order of {coupon.min_purchase_amount} required."
            )
        if coupon.discount_type == Coupon.PERCENTAGE:
            discount = (cart_total * coupon.discount_value / 100).quantize(Decimal('0.01'))
        else:
            discount = coupon.discount_value
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)

        return discount


class CouponStatsSerializer(serializers.Serializer):
    """
    Usage statistics for a coupon - seller analytics.
    GET /promotions/coupons/<id>/stats/
    """

    def to_representation(self, coupon: Coupon):
        usages = coupon.usages.all()
        agg = usages.aggregate(
            total_uses=Count('id'),
            total_discount=Sum('discount_amount'),
            unique_users=Count('user', distinct=True),
        )
        return {
            'code':            coupon.code,
            'total_uses':      agg['total_uses'] or 0,
            'total_discount':  str(agg['total_discount'] or Decimal('0.00')),
            'unique_users':    agg['unique_users'] or 0,
            'usage_limit':     coupon.usage_limit,
            'uses_remaining':  coupon.uses_remaining,
            'is_active':       coupon.is_currently_active,
        }

# COUPON USAGE

class CouponUsageSerializer(serializers.ModelSerializer):
    """Single coupon usage record."""
    coupon_code     = serializers.CharField(source='coupon.code',        read_only=True)
    order_number    = serializers.CharField(source='order.order_number', read_only=True)
    user_email      = serializers.EmailField(source='user.email',        read_only=True)

    class Meta:
        model = CouponUsage
        fields = ['id', 'coupon_code', 'order_number', 'user_email', 'discount_amount', 'used_at']
        read_only_fields = fields


class CouponUsageListSerializer(serializers.ModelSerializer):
    """Lightweight usage list - coupon code + order + date"""
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = CouponUsage
        fields = ['id', 'coupon_code', 'order_number', 'discount_amount', 'used_at']
        read_only_fields = fields


class CouponUsageStatsSerializer(serializers.Serializer):
    """
    Aggregated coupon usage analytics for a seller
    GET /promotions/coupons/usage/stats/
    """

    def to_representation(self, queryset):
        agg = queryset.aggregate(
            total_uses=Count('id'),
            total_discount=Sum('discount_amount'),
            unique_coupons=Count('coupon', distinct=True),
            unique_users=Count('user', distinct=True),
        )
        top_coupons = (
            queryset.values('coupon__code').annotate(uses=Count('id'), saved=Sum('discount_amount')).order_by('-uses')[:5]
        )
        return {
            'total_uses': agg['total_uses'] or 0,
            'total_discount': str(agg['total_discount'] or Decimal('0.00')),
            'unique_coupons': agg['unique_coupons'] or 0,
            'unique_users': agg['unique_users'] or 0,
            'top_coupons': list(top_coupons),
        }


#DEALS & SALES

class _ProductMiniSerializer(serializers.ModelSerializer):
    """Minimal product shape used inside deal/sale serializers."""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_at_price', 'rating_average', 'primary_image']
        read_only_fields = fields
    
    def get_primary_image(self, obj):
        return _primary_image(obj)

class FlashSaleSerializer(serializers.ModelSerializer):
    """Full flash sale details."""

    product = _ProductMiniSerializer(many=True, read_only=True)
    market_name = serializers.CharField(source='market.market_name', read_only=True)
    is_live = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ended = serializers.ReadOnlyField()
    seconds_remaining = serializers.SerializerMethodField()

    class Meta:
        model = FlashSale
        fields = [
            'id', 'market_name', 'title', 'description',
            'discount_percent', 'products',
            'starts_at', 'ends_at',
            'is_active', 'is_live', 'is_upcoming', 'is_ended',
            'seconds_remaining',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_seconds_remaining(self, obj):
        if obj.is_live:
            return max(0, int((obj.ends_at - timezone.now()).total_seconds()))
        return 0


class FlashSaleCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new flash sale. Seller only.
    POST /promotions/flash-sales/
    """
    product_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)

    class Meta:
        model = FlashSale
        fields = ['title', 'description', 'discount_percent', 'starts_at', 'ends_at', 'is_active', 'product_ids']
        extra_kwargs = {
            'title':               {'required': True},
            'discount_percentage': {'required': True},
            'starts_at':           {'required': True},
            'ends_at':             {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['ends_at'] <= attrs['starts_at']:
            raise serializers.ValidationError({'ends_at': 'Must be after starts_at.'})
        market = self.context['request'].user.markets.filter(is_active=True).first()
        if not market:
            raise serializers.ValidationError("You must have an active market to create flash sales.")
        self._market = market
        return attrs
    
    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids', [])
        sale = FlashSale.objects.create(market=self._market, **validated_data)
        if product_ids:
            products = Product.objects.filter(pk__in=product_ids, market=self._market, is_active=True)
            sale.products.set(products)
        return sale


class FlashSaleUpdateSerializer(serializers.ModelSerializer):
    """
    Updates flash sale details. Seller only
    PATCH /promotions/flash-sales/<id>/
    """
    product_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    
    class Meta:
        model = FlashSale
        fields = ['title', 'description', 'discount_percent', 'starts_at', 'ends_at', 'is_active', 'product_ids']
        extra_kwargs = {f: {'required': False} for f in fields}
    
    def validate(self, attrs):
        sa = attrs.get('starts_at', self.instance.starts_at)
        ea = attrs.get('ends_at',   self.instance.ends_at)
        if ea <= sa:
            raise serializers.ValidationError({'ends_at': 'Must be after starts_at.'})
        return attrs
    
    def update(self, instance, validated_data):
        product_ids = validated_data.pop('product_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if product_ids is not None:
            products = Product.objects.filter(pk__in=product_ids, market=instance.market, is_active=True)
            instance.products.set(products)
        return instance
        

class DealOfTheDaySerializer(serializers.ModelSerializer):
    """
    Current deal of the day - the active flash sale with the highest discoun.
    GET /promotions/deal-of-the-day/
    """
    products = _ProductMiniSerializer(many=True, read_only=True)
    market_name = serializers.CharField(source='market.market_name', read_only=True)
    seconds_remaining = serializers.SerializerMethodField()

    class Meta:
        model = FlashSale
        fields = ['id', 'market_name', 'title', 'discount_percent', 'products', 'ends_at', 'seconds_remaining']
        read_only_fields = fields
    
    def get_seconds_remaining(self, obj):
        return max(0, int((obj.ends_at - timezone.now()).total_seconds()))

class ClearanceSaleSerializer(serializers.ModelSerializer):
    """Clearance promotion - products with discount > 40%."""
    products = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'description', 'discount_percent', 'products', 'ends_at', 'image_url']
        read_only_fields = fields
    
    def get_products(self, obj):
        return _ProductMiniSerializer(obj.products.filter(is_active=True)[:8], many=True).data
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

class SeasonalSaleSerializer(serializers.ModelSerializer):
    """Seasonal promotion card."""
    products = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    is_live = serializers.ReadOnlyField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'description', 'discount_percent', 'products', 'starts_at', 'ends_at', 'is_live', 'image_url']
        read_only_fields = fields
    
    def get_products(self, obj):
        return _ProductMiniSerializer(obj.products.filter(is_active=True)[:8], many=True).data
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class BundleDealsSerializer(serializers.ModelSerializer):
    """Bundle / combo deal."""
    products = _ProductMiniSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    is_live = serializers.ReadOnlyField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'description', 'discount_percent', 'products', 'starts_at', 'ends_at', 'is_live', 'image_url']
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class ActiveDealsSerializer(serializers.ModelSerializer):
    """All currently live deals (flash sales + promotions) - lightweight"""
    image_url = serializers.SerializerMethodField()
    is_live = serializers.ReadOnlyField()
    deal_type = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'discount_percent', 'ends_at', 'is_live', 'image_url', 'deal_type']
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
    
    def get_deal_type(self, obj):
        return obj.promo_type

class UpcomingDealsSerializer(serializers.ModelSerializer):
    """Scheduled deals that haven't started yet."""
    image_url = serializers.SerializerMethodField()
    is_upcoming = serializers.ReadOnlyField()
    starts_in_hours = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'discount_percent', 'starts_at', 'ends_at', 'is_upcoming', 'starts_in_hours', 'image_url']
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
    
    def get_starts_in_hours(self, obj):
        delta = obj.starts_at - timezone.now()
        return max(0, round(delta.total_seconds() / 3600, 1))

class ExpiredDealsSerializer(serializers.ModelSerializer):
    """Past / expired deals for the seller's history view."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'promo_type', 'discount_percent', 'starts_at', 'ends_at', 'image_url']
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
    

#PROMOTIONS
class PromotionSerializer(serializers.ModelSerializer):
    """Basic promotion info - nested reference."""
    image_url = serializers.SerializerMethodField()
    is_live = serializers.ReadOnlyField()
    market_name = serializers.CharField(source='market.market_name', read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id', 'market_name', 'title', 'description',
            'promo_type', 'discount_percent', 'image_url',
            'starts_at', 'ends_at',
            'is_active', 'is_featured', 'is_live',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
    

class PromotionListSerializer(serializers.ModelSerializer):
    """Lightweight promotion row for listing pages."""
    image_url = serializers.SerializerMethodField()
    is_live = serializers.ReadOnlyField()

    class Meta:
        model = Promotion
        fields = ['id', 'title', 'promo_type', 'discount_percent', 'starts_at', 'ends_at', 'is_live', 'image_url']
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

class PromotionDetailSerializer(serializers.ModelSerializer):
    """Complete promotion with products and market info."""
    products = _ProductMiniSerializer(many=True, read_only=True)
    image_urls = serializers.SerializerMethodField()
    market_name = serializers.CharField(source='market.market_name', read_only=True)
    is_live = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ended = serializers.ReadOnlyField()

    class Meta:
        model = Promotion
        fields = [
            'id', 'market_name', 'title', 'description',
            'promo_type', 'discount_percent', 'image_url', 'products',
            'starts_at', 'ends_at',
            'is_active', 'is_featured', 'is_live', 'is_upcoming', 'is_ended',
            'view_count', 'click_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


#PROMOTIONS

class PromotionCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new promotion campaign, Seller or admin
    POST /promotions/
    """
    product_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    
    class Meta:
        model = Promotion
        fields = [
            'title', 'description', 'promo_type',
            'discount_percent', 'image',
            'starts_at', 'ends_at',
            'is_active', 'is_featured',
            'product_ids',
        ]
        extra_kwargs = {
            'title':      {'required': True},
            'promo_type': {'required': True},
            'starts_at':  {'required': True},
            'ends_at':    {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['ends_at'] <= attrs['starts_at']:
            raise serializers.ValidationError({'ends_at': 'Must be after starts_at.'})
        user = self.context['request'].user
        market = None if user.is_staff else user.markets.filter(is_active=True).first()
        if not user.is_staff and not market:
            raise serializers.ValidationError("You must have an active market to create promotions.")
        self._market = market
        return attrs
    
    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids', [])
        promo = Promotion.objects.create(market=self._market, **validated_data)
        if product_ids:
            qs = Product.objects.filter(pk__in=product_ids, is_active=True)
            if self._market:
                qs = qs.filter(market=self._market)
            promo.products.set(qs)
        return promo


class PromotionUpdateSerializer(serializers.ModelSerializer):
    """
    Updates promotion detials, seller only
    PATCH /promotions/<id>/
    """
    product_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = Promotion
        fields = [
            'title', 'description', 'promo_type',
            'discount_percent', 'image',
            'starts_at', 'ends_at',
            'is_active', 'is_featured',
            'product_ids',
        ]
        extra_kwargs = {f: {'required': False} for f in fields}
    
    def validate(self, attrs):
        sa = attrs.get('starts_at', self.instance.starts_at)
        ea = attrs.get('ends_at', self.instance.ends_at)
        if ea <= sa:
            raise serializers.ValidationError({'ends_at': "Must be after starts_at."})
        return attrs
    
    def update(self, instance, validated_data):
        product_ids = validated_data.pop('product_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if product_ids is not None:
            qs = Product.objects.filter(pk__in=product_ids, is_active=True)
            instance.products.set(qs)
        return instance


class PromotionStatsSerializer(serializers.Serializer):
    """
    Promotion performance stats for seller analytics
    GET /promotions/<id>/stats/
    """

    def to_representation(self, promo: Promotion):
        return {
            'title':         promo.title,
            'promo_type':    promo.promo_type,
            'view_count':    promo.view_count,
            'click_count':   promo.click_count,
            'ctr':           round(promo.click_count / promo.view_count * 100, 2) if promo.view_count else 0,
            'product_count': promo.products.count(),
            'is_live':       promo.is_live,
            'is_ended':      promo.is_ended,
            'days_remaining': max(0, (promo.ends_at - timezone.now()).days) if not promo.is_ended else 0,
        }