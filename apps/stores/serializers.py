"""
stores/serializers.py
======================
Market / Store  (13 serializers)
  MarketSerializer
  MarketCreateSerializer
  MarketUpdateSerializer
  MarketDeleteSerializer
  MarketDetailSerializer
  MarketListSerializer
  MarketPublicSerializer
  MarketSellerSerializer
  MarketStatsSerializer
  MarketSearchSerializer
  MarketSettingsSerializer
  MarketVerificationSerializer
  MarketAnalyticsSerializer

Market Discovery  (6 serializers)
  FeaturedMarketsSerializer
  PopularMarketsSerializer
  MarketBrowseSerializer
  MarketCategorySerializer
  NearbyMarketsSerializer
  TrendingMarketsSerializer

Market Reviews  (7 serializers)
  MarketReviewSerializer
  MarketReviewCreateSerializer
  MarketReviewUpdateSerializer
  MarketReviewDeleteSerializer
  MarketReviewListSerializer
  MarketReviewStatsSerializer
  MarketReviewDetailSerializer

Market Followers  (5 serializers)
  MarketFollowerSerializer
  FollowMarketSerializer
  UnfollowMarketSerializer
  MarketFollowersListSerializer
  FollowedMarketsSerializer
"""



from decimal import Decimal
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import *
from .models import *

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rating_breakdown(market: Market) -> dict:
    """
    Returns count of each star level for a market
    """
    breakdown = {str(i): 0 for i in range(1, 6)}
    qs = MarketReview.objects.filter(market=market, is_approved=True).values('rating').annotate(count=Count('id'))
    for row in qs:
        star = str(int(row['rating']))
        breakdown[star] = row['count']
    return breakdown



# ═════════════════════════════════════════════════════════════════════════════
# MARKET / STORE
# ═════════════════════════════════════════════════════════════════════════════
class MarketSerializer(serializers.ModelSerializer):
    """
    Basic market info - used internally as a nested reference
    """
    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 'description',
            'logo_url', 'banner_url', 'is_verified', 'is_active',
            'rating_average', 'total_sales', 'created_at',
        ]
        read_only_fields = fields
    
    def get_logo_url(self, obj: Market) -> str:
        return obj.logo.url if obj.logo else None
    
    def get_banner_url(self, obj: Market) -> str:
        return obj.banner_image.url if obj.banner_image else None
    

# ─────────────────────────────────────────────────────────────────────────────
class MarketCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new market for the authenticated seller
    POST /stores/markets/
    """

    class Meta:
        model = Market
        fields = [
            'market_name', 'description', 'business_email', 
            'business_phone', 'business_address', 'tax_id',
        ]
        extra_kwargs = {
            'market_name': {'required': True}
        }
    
    def validate(self, attrs):
        user = self.context['request'].user
        if Market.objects.filter(seller=user).exists():
            raise serializers.ValidationError(
                "You already have a market. Update it instead of creating a new one."
            )
        return attrs
    
    def create(self, validated_data):
        return Market.objects.create(
            seller = self.context['request'].user,
            is_active = False,
            **validated_data
        )
        
# ─────────────────────────────────────────────────────────────────────────────
class MarketUpdateSerializer(serializers.ModelSerializer):
    """
    Updates mutable market fields.
    PATCH /stores/markets/<id>/
    Accepts multipart/form-data for logo / banner uploads.
    """
    logo = serializers.ImageField(required = False)
    banner_image = serializers.ImageField(required = False)

    class Meta:
        model = Market
        fields = [
            'description', 'business_email', 'business_phone', 'business_address',
            'tax_id', 'logo', 'banner_image',
        ]
        extra_kwargs = {f: {"required": False} for f in fields}
    
    def update(self, instance, validated_data):
        new_logo = validated_data.pop('logo', None)
        new_banner = validated_data.pop('banner_image', None)

        if new_logo:
            if instance.logo:
                instance.logo.delete(save=False)
            instance.logo = new_logo
        
        if new_banner:
            if instance.banner_image:
                instance.banner_image.delete(save=False)
            instance.logo = new_banner
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# ─────────────────────────────────────────────────────────────────────────────
class MarketDeleteSerializer(serializers.Serializer):
    """
    Soft deletes (deactivates) a market.
    DELETE /stores/markets/<id>/
    Requires password confirmation to prevent accidents
    """
    password = serializers.CharField(write_only = True)
    
    def validate_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value
    
    def save(self):
        market = self.context['market']
        market.is_active = False
        market.save(update_fields=['is_active'])

# ─────────────────────────────────────────────────────────────────────────────
class MarketDetailSerializer(serializers.ModelSerializer):
    """
    Full market detail - owner / admin view with all fields
    GET /stores/markets/<id>/detail/
    """

    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    seller_email = serializers.EmailField(source='seller.email', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    review_count = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'seller_email', 'seller_name', 'market_name', 'slug', 'description',
            'logo_url', 'banner_url', 'business_email', 'business_phone', 'business_address',
            'tax_id', 'is_verified', 'is_active', 'rating_average', 'total_sales', 'review_count',
            'follower_count', 'created_at', 'updated_at',
        ]
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    
    def get_banner_url(self, obj):
        return obj.banner_image.url if obj.banner_image else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_follower_count(self, obj):
        # plug in obj.followers.count() when market followers model exists.
        return 0


# ─────────────────────────────────────────────────────────────────────────────
class MarketListSerializer(serializers.ModelSerializer):
    """
    Lightweight market list item - optimized for listing pages/
    GET /stores/markets/
    """
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 
            'logo_url', 'is_verified', 
            'rating_average', 'total_sales',
        ]
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    

# ─────────────────────────────────────────────────────────────────────────────
class MarketPublicSerializer(serializers.ModelSerializer):
    """
    Public market card visible to unauthenticated buyers.
    GET /stores/markets/<slug>/
    """

    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 'description', 'logo_url', 'banner_url', 
            'business_email', 'business_address', 'is_verified', 'rating_average', 
            'total_sales', 'review_count', 'created_at',
        ]
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    
    def get_banner_url(self, obj):
        return obj.banner_image.url if obj.banner_image else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    



# ═════════════════════════════════════════════════════════════════════════════
# SELLER'S OWN MARKET
# ═════════════════════════════════════════════════════════════════════════════
class MarketSellerSerializer(serializers.ModelSerializer):
    """
    Seller's own management view - includes private fields
    GET /stores/my-market/
    """

    logo_url        = serializers.SerializerMethodField()
    banner_url      = serializers.SerializerMethodField()
    review_count    = serializers.SerializerMethodField()
    product_count   = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 'description', 'logo_url', 'banner_url', 
            'business_email', 'business_phone', 'business_address', 'tax_id', 'is_verified',
            'is_active', 'rating_average', 'total_sales', 'review_count', 'product_count', 'created_at', 
            'updated_at', 
        ]
        read_only_fields = fields

    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    
    def get_banner_url(self, obj):
        return obj.banner_image.url if obj.banner_image else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


# ─────────────────────────────────────────────────────────────────────────────
class MarketStatsSerializer(serializers.Serializer):
    """
    Performance statistics for the seller dashboard
    GET /stores/my-market/stats/
    """

    def to_representation(self, instance: Market):
        approved_reviews = instance.reviews.filter(is_approved=True)
        return {
            'total_sales':              instance.total_sales,
            'rating_average':           str(instance.rating_average),
            'total_reviews':            approved_reviews.count(),
            'total_active_products':    instance.products.filter(is_active=True).count(),
            'is_verified':              instance.is_verified,
            'is_active':                instance.is_active,
            'member_for_days':          (timezone.now() - instance.created_at).days,
            'rating_breakdown':         _rating_breakdown(instance),
        }

# ─────────────────────────────────────────────────────────────────────────────
class MarketSettingsSerializer(serializers.ModelSerializer):
    """
    Manages market settings toggled by the seller
    PATCH /stores/my-market/settings/
    """
    class Meta:
        model = Market
        fields = ['is_active', 'business_email', 'business_phone', 'business_address', 'tax_id']
        extra_kwargs = {f: {'required': False} for f in fields}
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
# ─────────────────────────────────────────────────────────────────────────────
class MarketVerificationSerializer(serializers.Serializer):
    """
    Seller submits verification request.
    POST /stores/my-market/verify/
    Admin-only approval is handled seperately
    """
    tax_id = serializers.CharField(max_length = 50)
    business_address = serializers.CharField()
    business_phone = serializers.CharField(max_length=20)

    def save(self):
        market = self.context["market"]
        market.tax_id = self.validated_data['tax_id']
        market.business_address = self.validated_data['business_address']
        market.business_phone = self.validated_data['business_phone']
        market.save(update_fields=['tax_id', 'business_address', 'business_address'])

        # TODO: trigger admin notification / verification workflow
    
# ─────────────────────────────────────────────────────────────────────────────
class MarketAnalyticsSerializer(serializers.Serializer):
    """
    Detailed analytics for the seller dashboard
    GET /stores/my-market/analytics/
    Plug in real aggregations from orders/products as those apps grow
    """

    def to_representation(self, instance: Market):
        now = timezone.now()
        thirty = now - timezone.timedelta(days=30)
        seven = now - timezone.timedelta(days=7)
        
        reviews_30d = instance.reviews.filter(is_approved=True, created_at__gte=thirty).count()
        reviews_7d = instance.reviews.filter(is_approved=True, created_at__gte=seven).count()

        return {
            'total_sales':              instance.total_sales,
            'rating_average':           str(instance.rating_average),
            'total_reviews':            instance.reviews.filter(is_approved=True).count(),
            'reviews_last_30_days':     reviews_30d,
            'reviews_last_7_days':      reviews_7d,
            'active_products':          instance.products.filter(is_active=True).count(),
            'low_stock_products':       instance.products.filter(is_active=True, stock_quantity__lte=10).count(),
            'rating_breakdown':         _rating_breakdown(instance)
            # Plug in when orders app is ready:
            # 'orders_last_30_days': instance.orders.filter(created_at__gte=thirty).count(),
            # 'revenue_last_30_days': instance.orders.filter(...).aggregate(...)['total'],
        }


# ═════════════════════════════════════════════════════════════════════════════
# MARKET DISCOVERY
# ═════════════════════════════════════════════════════════════════════════════

class MarketSearchSerializer(serializers.ModelSerializer):
    """
    Search result item - minimal data for fast rendering
    GET /stores/markets/search/?q=...
    """
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 'logo_url', 'is_verified', 'rating_average',
        ]
        read_only_fields = fields

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    

class FeaturedMarketsSerializer(serializers.ModelSerializer):
    """
    Featured / promoted markets for the homepage.
    GET /stores/markets/featured/
    'Featured' = verified, active, sorted by total_salse desc.
    """

    logo_url = serializers.SerializerMethodField()
    class Meta:
        model = Market
        fields = ['id', 'market_name', 'slug', 'logo_url', 'is_verified', 'rating_average']
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    

class PopularMarketsSerializer(serializers.ModelSerializer):
    """
    Most popular markets ordered by total_sales
    GET /stores/markets/popular/
    """

    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = ['id', 'market_name', 'slug', 'logo_url', 'rating_average', 'total_sales']
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
        

class MarketBrowseSerializer(serializers.ModelSerializer):
    """
    Market browsing page item - includes enough data for a buyer browse card.
    GET /stores/markets/browse/
    """

    logo_url = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 'description', 
            'logo_url', 'is_verified', 'rating_average', 'total_sales', 'review_count',
        ]
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    

class MarketCategorySerializer(serializers.Serializer):
    """
    Lists markets grouped / filtered by a product category
    GET /stores/markets/by-category/<category_id>/
    Returns the same shape as MarketBrowseSerializer
    """

    def to_representation(self, instance: Market):
        return {
            'id':               instance.id,
            'market_name':      instance.market_name,
            'slug':             instance.slug,
            'logo_url':         instance.logo.url if instance.logo else None, 
            'is_verified':      instance.is_verified,
            'rating_average':   str(instance.rating_average),
            'total_sales':      instance.total_sales,
        }

        
class TrendingMarketsSerializer(serializers.ModelSerializer):
    """
    Currently trending markets (most reviews in last 7 days).
    GET /stores/markets/trending/
    """

    logo_url = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = ['id', 'market_name', 'slug', 'logo_url', 'rating_average', 'recent_reviews']
        read_only_fields = fields

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None
    
    def get_recent_reviews(self, obj):
        since = timezone.now() - timezone.timedelta(days=7)
        return obj.reviews.filter(is_approved=True, created_at__gte=since).count()


    
    






















# ═════════════════════════════════════════════════════════════════════════════
# MARKET REVIEWS
# ═════════════════════════════════════════════════════════════════════════════

class MarketReviewSerializer(serializers.ModelSerializer):
    """Full review details — used as a base / nested serializer."""
    reviewer_name = serializers.SerializerMethodField()
    reviewer_avatar = serializers.SerializerMethodField()

    class Meta:
        model  = MarketReview
        fields = [
            'id', 'reviewer_name', 'reviewer_avatar',
            'rating', 'comment', 'is_approved',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_reviewer_avatar(self, obj):
        return obj.user.get_avatar_url()


# ─────────────────────────────────────────────────────────────────────────────

class MarketReviewCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new market review.
    POST /stores/markets/<id>/reviews/
    One review per order enforced at model level.
    """

    class Meta:
        model  = MarketReview
        fields = ['order', 'rating', 'comment']
        extra_kwargs = {
            'order':   {'required': True},
            'comment': {'required': False},
        }

    def validate(self, attrs):
        user   = self.context['request'].user
        market = self.context['market']
        order  = attrs.get('order')

        # Order must belong to this user and this market
        if order and order.user_id != user.pk:
            raise serializers.ValidationError(
                {"order": "You can only review orders that belong to you."}
            )
        if order and order.market_id != market.pk:
            raise serializers.ValidationError(
                {"order": "This order is not from this market."}
            )
        if MarketReview.objects.filter(market=market, user=user, order=order).exists():
            raise serializers.ValidationError(
                "You have already reviewed this market for this order."
            )
        return attrs

    def create(self, validated_data):
        return MarketReview.objects.create(
            market=self.context['market'],
            user=self.context['request'].user,
            **validated_data,
        )


# ─────────────────────────────────────────────────────────────────────────────

class MarketReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Edits own review (rating and comment only).
    PATCH /stores/markets/reviews/<id>/
    """

    class Meta:
        model  = MarketReview
        fields = ['rating', 'comment']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────

class MarketReviewDeleteSerializer(serializers.Serializer):
    """
    Validates ownership before deletion.
    DELETE /stores/markets/reviews/<id>/
    """

    def validate(self, attrs):
        review = self.context['review']
        user   = self.context['request'].user
        if review.user_id != user.pk and not user.is_staff:
            raise serializers.ValidationError(
                "You can only delete your own reviews."
            )
        return attrs

    def save(self):
        self.context['review'].delete()


# ─────────────────────────────────────────────────────────────────────────────

class MarketReviewListSerializer(serializers.ModelSerializer):
    """
    Lightweight review list item.
    GET /stores/markets/<id>/reviews/
    """
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model  = MarketReview
        fields = ['id', 'reviewer_name', 'rating', 'comment', 'created_at']
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


# ─────────────────────────────────────────────────────────────────────────────

class MarketReviewStatsSerializer(serializers.Serializer):
    """
    Rating breakdown for a market's review section.
    GET /stores/markets/<id>/reviews/stats/
    """

    def to_representation(self, instance: Market):
        approved = instance.reviews.filter(is_approved=True)
        avg      = approved.aggregate(avg=Avg('rating'))['avg'] or 0
        return {
            'total_reviews':    approved.count(),
            'average_rating':   round(float(avg), 2),
            'rating_breakdown': _rating_breakdown(instance),
        }


# ─────────────────────────────────────────────────────────────────────────────

class MarketReviewDetailSerializer(serializers.ModelSerializer):
    """
    Full review with user info — for moderation / detail page.
    GET /stores/markets/reviews/<id>/
    """
    reviewer_name   = serializers.SerializerMethodField()
    reviewer_avatar = serializers.SerializerMethodField()
    reviewer_email  = serializers.SerializerMethodField()
    order_number    = serializers.SerializerMethodField()

    class Meta:
        model  = MarketReview
        fields = [
            'id', 'reviewer_name', 'reviewer_avatar', 'reviewer_email',
            'order_number', 'rating', 'comment',
            'is_approved', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_reviewer_avatar(self, obj):
        return obj.user.get_avatar_url()

    def get_reviewer_email(self, obj):
        # Only expose to staff
        request = self.context.get('request')
        if request and request.user.is_staff:
            return obj.user.email
        return None

    def get_order_number(self, obj):
        return obj.order.order_number if obj.order else None


# ═════════════════════════════════════════════════════════════════════════════
# MARKET FOLLOWERS
# Note: These serializers are implemented using a simple in-memory pattern.
# When you add a MarketFollower model, swap the placeholder logic below.
# ═════════════════════════════════════════════════════════════════════════════

class MarketFollowerSerializer(serializers.Serializer):
    """
    Single follower record.
    Shape: { user_id, username, avatar_url, followed_at }
    Plug in real data once MarketFollower model exists.
    """
    user_id     = serializers.IntegerField()
    username    = serializers.CharField()
    avatar_url  = serializers.CharField(allow_null=True)
    followed_at = serializers.DateTimeField()


# ─────────────────────────────────────────────────────────────────────────────

class FollowMarketSerializer(serializers.Serializer):
    """
    Follows a market.
    POST /stores/markets/<id>/follow/
    """

    def validate(self, attrs):
        # Replace with: if MarketFollower.objects.filter(...).exists(): raise
        return attrs

    def save(self):
        # Replace with: MarketFollower.objects.get_or_create(user=..., market=...)
        pass


# ─────────────────────────────────────────────────────────────────────────────

class UnfollowMarketSerializer(serializers.Serializer):
    """
    Unfollows a market.
    DELETE /stores/markets/<id>/follow/
    """

    def save(self):
        # Replace with: MarketFollower.objects.filter(user=..., market=...).delete()
        pass


# ─────────────────────────────────────────────────────────────────────────────

class MarketFollowersListSerializer(serializers.Serializer):
    """
    Lists all followers of a market.
    GET /stores/markets/<id>/followers/
    Returns a placeholder until MarketFollower model is added.
    """

    def to_representation(self, instance: Market):
        return {
            'market':         instance.market_name,
            'follower_count': 0,   # replace with instance.followers.count()
            'followers':      [],  # replace with MarketFollowerSerializer(qs, many=True).data
        }


# ─────────────────────────────────────────────────────────────────────────────

class FollowedMarketsSerializer(serializers.ModelSerializer):
    """
    Markets the authenticated user is following.
    GET /stores/markets/following/
    Returns the same shape as MarketListSerializer.
    """
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model  = Market
        fields = ['id', 'market_name', 'slug', 'logo_url', 'is_verified', 'rating_average']
        read_only_fields = fields

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None