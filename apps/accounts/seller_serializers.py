
"""
Seller serializers — backed by the Market model.
Replace the 5 SellerProfile-based serializers in accounts/serializers.py with these.
Also update the import at the top of serializers.py:
  from markets.models import Market   (adjust app path to match yours)
"""


from django.db import transaction
from rest_framework import serializers
from apps.stores.models import Market


# ─────────────────────────────────────────────────────────────────────────────
# BecomeSellerSerializer  (was: creates SellerProfile)
# ─────────────────────────────────────────────────────────────────────────────

class BecomeSellerSerializer(serializers.ModelSerializer):
    """
    Converts a regular user into a seller by creating their Market.
    POST /accounts/me/become-seller/
    
    The market starts inactive (is_active = False) until admin approves.
    or you can flip that default if your flow auto-approves.
    """
    class Meta:
        model = Market
        fields = [
            'market_name', 'description', 
            'business_email', 'business_phone', 'business_address',
            'tax_id',
        ]
        extra_kwargs = {
            'market_name':      {'required': True},
            'business_phone':   {'required': True},
        }
    
    def validate(self, attrs: dict) -> dict:
        user = self.context['request'].user
        if user.is_seller:
            raise serializers.ValidationError("You already have a seller account.")
        if Market.objects.filter(seller=user).exists():
            raise serializers.ValidationError("A market already exists for this account.")
        return attrs
    
    @transaction.atomic
    def save(self, **kwargs) -> Market:
        user = self.context['request'].user
        validated_data = dict(self.validated_data)
        market = Market.objects.create(
            seller=user,
            is_active=False,
            total_sales=0,
            **validated_data,
        )
        user.is_seller = True
        user.save(update_fields=['is_seller'])
        return market




# ─────────────────────────────────────────────────────────────────────────────
# SellerProfileSerializer  (own full market — authenticated seller)
# ─────────────────────────────────────────────────────────────────────────────
class SellerProfileSerializer(serializers.ModelSerializer):
    """
    Full market detail for the authenticated seller.
    GET /accounts/me/seller/
    """
    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source='seller.email', read_only=True)

    class Meta:
        model = Market
        fields = [
            'id', 'owner_email', 'market_name', 'slug', 'description',
            'logo_url', 'banner_url', 'business_email', 'business_phone',
            'business_address', 'tax_id', 'is_verified', 'is_active', 
            'rating_average', 'total_sales', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_logo_url(self, obj: Market) -> str | None:
        return obj.logo.url if obj.logo else None
    
    def get_banner_url(self, obj: Market) -> str | None:
        return obj.banner_image.url if obj.banner_image else None




# ─────────────────────────────────────────────────────────────────────────────
# SellerProfileUpdateSerializer  
# ─────────────────────────────────────────────────────────────────────────────

class SellerProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Updates mutable market fields
    PATCH /accounts/me/seller/update/
    Accepts multipart/form-data for logo and banner uploads.
    """

    logo         = serializers.ImageField(required = False)
    banner_image = serializers.ImageField(required = False)
    class Meta:
        model = Market
        fields = [
            'description', 'market_name', 
            'business_email', 'business_phone', 'business_address',
            'logo', 'banner_image',
        ]
        extra_kwargs = {f: {"required": False} for f in fields}

    def update(self, instance: Market, validated_data: dict) -> Market:
        new_logo = validated_data.pop('logo', None)
        new_banner_image = validated_data.pop('banner_image', None)

        if new_logo:
            if instance.logo:
                instance.logo.delete(save=False)
            instance.logo = new_logo
        
        if new_banner_image:
            if instance.banner_image:
                instance.banner_image.delete(save=False)
            instance.banner_image = new_banner_image
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

 
# ─────────────────────────────────────────────────────────────────────────────
# SellerPublicSerializer  (buyer-facing market card)
# ─────────────────────────────────────────────────────────────────────────────

class SellerPublicSerializer(serializers.ModelSerializer):
    """
    Public market card visible to unauthenticated buyers.
    GET /accounts/sellers/<seller_id>/
    """
    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'market_name', 'slug', 'description', 
            'logo_url', 'banner_url',
            'business_email', 'business_address', 'is_verified', 
            'rating_average', 'total_sales', 'created_at',
        ]
        read_only_fields = fields
    
    def get_logo_url(self, obj: Market) -> str | None:
        return obj.logo.url if obj.logo else None
    
    def get_banner_url(self, obj: Market) -> str | None:
        return obj.banner_image.url if obj.banner_image else None


# ─────────────────────────────────────────────────────────────────────────────
# SellerStatsSerializer
# ─────────────────────────────────────────────────────────────────────────────

class SellerStatsSerializer(serializers.Serializer):
    """
    GET /accounts/me/seller/stats/
    The view passes the Market instance directly
    """

    def to_representation(self, instance: Market) -> dict:
        from django.utils import timezone
        return{
            'market_name': instance.market_name,
            'total_sales': instance.total_sales,
            'rating_average': str(instance.rating_average),
            'is_verified': instance.is_verified,
            'is_active': instance.is_active,
            'member_for_days': (timezone.now() - instance.created_at).days,
            # need to plug real aggregations as orders and products grow
        }
