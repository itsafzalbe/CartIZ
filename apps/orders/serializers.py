"""
orders/serializers.py
======================
Orders          (15) OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer,
                     OrderDeleteSerializer, OrderDetailSerializer, OrderListSerializer,
                     OrderBuyerListSerializer, OrderSellerListSerializer,
                     OrderStatusUpdateSerializer, OrderCancelSerializer,
                     OrderTrackingSerializer, OrderHistorySerializer,
                     OrderSearchSerializer, OrderStatsSerializer, OrderInvoiceSerializer

Order Items      (3) OrderItemSerializer, OrderItemListSerializer, OrderItemDetailSerializer

Order Addresses  (3) OrderAddressSerializer, OrderShippingAddressSerializer,
                     OrderBillingAddressSerializer

Order Shipping  (11) OrderShippingSerializer, OrderShippingCreateSerializer,
                     OrderShippingUpdateSerializer, OrderShippingTrackingSerializer,
                     ShippingMethodSerializer, ShippingMethodCreateSerializer,
                     ShippingMethodUpdateSerializer, ShippingMethodDeleteSerializer,
                     ShippingMethodListSerializer, CalculateShippingCostSerializer,
                     TrackingUpdateSerializer
"""

import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers
from apps.accounts.models import User, UserAddress
from apps.cart.models import Cart
from .models import *

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
TAX_RATE = Decimal('0.12')
CANCELLABLE_STATUSES = {Order.ORDER_PENDING, Order.CONFIRMED}

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _generate_order_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"

# ═════════════════════════════════════════════════════════════════════════════
# ORDER ITEMS
# ═════════════════════════════════════════════════════════════════════════════
class OrderItemSerializer(serializers.ModelSerializer):
    """Single order item - read-only."""

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'variant_name', 'sku',
            'quantity', 'unit_price', 'subtotal',
            'discount', 'tax_amount', 'total',
            'created_at',
        ]
        read_only_fields = fields
    
class OrderItemListSerializer(serializers.ModelSerializer):
    """Lightweight item row used inside order lists."""

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'variant_name', 'quantity', 'unit_price', 'total']
        read_only_fields = fields

class OrderItemDetailSerializer(serializers.ModelSerializer):
    """Order item with live product snapshots."""
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'product_slug', 'variant_name', 'sku',
            'quantity', 'unit_price', 'subtotal',
            'discount', 'tax_amount', 'total',
            'primary_image', 'created_at',
        ]
        read_only_fields = fields
    
    def get_primary_image(self, obj):
        img = (
            obj.product.product_images.filter(is_primary=True).first()
            or obj.product.product_images.first()
        )
        return img.image.url if img else None

# ═════════════════════════════════════════════════════════════════════════════
# ORDER ADDRESSES
# ═════════════════════════════════════════════════════════════════════════════
class OrderAddressSerializer(serializers.ModelSerializer):
    """Both shipping and billing addresses for an order."""

    class Meta:
        model = OrderAddress
        fields = [
            'id', 'address_type', 'full_name', 'phone_number',
            'address_line_1', 'address_line_2',
            'city', 'state_province', 'postal_code', 'country',
            'created_at',
        ]
        read_only_fields = fields

class OrderShippingAddressSerializer(serializers.ModelSerializer):
    """Shipping address only."""
    class Meta:
        model = OrderAddress
        fields = [
            'id', 'full_name', 'phone_number',
            'address_line_1', 'address_line_2',
            'city', 'state_province', 'postal_code', 'country',
        ]
        read_only_fields = fields 














# ═════════════════════════════════════════════════════════════════════════════
# ORDER ADDRESSES
# ═════════════════════════════════════════════════════════════════════════════




class OrderBillingAddressSerializer(serializers.ModelSerializer):
    """Billing address only."""

    class Meta:
        model  = OrderAddress
        fields = [
            'id', 'full_name', 'phone_number',
            'address_line_1', 'address_line_2',
            'city', 'state_province', 'postal_code', 'country',
        ]
        read_only_fields = fields


# ═════════════════════════════════════════════════════════════════════════════
# SHIPPING METHODS
# ═════════════════════════════════════════════════════════════════════════════

class ShippingMethodSerializer(serializers.ModelSerializer):
    """Full shipping method detail."""
    delivery_estimate = serializers.SerializerMethodField()

    class Meta:
        model  = ShippingMethod
        fields = [
            'id', 'name', 'description', 'cost',
            'estimated_days_min', 'estimated_days_max',
            'delivery_estimate', 'is_active', 'created_at',
        ]
        read_only_fields = fields

    def get_delivery_estimate(self, obj):
        if obj.estimated_days_min and obj.estimated_days_max:
            return f"{obj.estimated_days_min}–{obj.estimated_days_max} business days"
        if obj.estimated_days_min:
            return f"From {obj.estimated_days_min} business days"
        return None


class ShippingMethodListSerializer(serializers.ModelSerializer):
    """Lightweight method row for checkout dropdowns."""
    delivery_estimate = serializers.SerializerMethodField()

    class Meta:
        model  = ShippingMethod
        fields = ['id', 'name', 'cost', 'delivery_estimate']
        read_only_fields = fields

    def get_delivery_estimate(self, obj):
        if obj.estimated_days_min and obj.estimated_days_max:
            return f"{obj.estimated_days_min}–{obj.estimated_days_max} days"
        return None


class ShippingMethodCreateSerializer(serializers.ModelSerializer):
    """
    Creates a new shipping method for the seller's market.
    POST /orders/shipping-methods/
    """

    class Meta:
        model  = ShippingMethod
        fields = ['name', 'description', 'cost', 'estimated_days_min', 'estimated_days_max', 'is_active']
        extra_kwargs = {
            'name': {'required': True},
            'cost': {'required': True},
        }

    def validate(self, attrs):
        market = self.context['request'].user.markets.filter(is_active=True).first()
        if not market:
            raise serializers.ValidationError("You must have an active market to create shipping methods.")
        self._market = market

        if ShippingMethod.objects.filter(market=market, name__iexact=attrs['name']).exists():
            raise serializers.ValidationError({"name": "A shipping method with this name already exists."})
        return attrs

    def create(self, validated_data):
        return ShippingMethod.objects.create(market=self._market, **validated_data)


class ShippingMethodUpdateSerializer(serializers.ModelSerializer):
    """
    Updates shipping method details. Seller only.
    PATCH /orders/shipping-methods/<id>/
    """

    class Meta:
        model  = ShippingMethod
        fields = ['name', 'description', 'cost', 'estimated_days_min', 'estimated_days_max', 'is_active']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ShippingMethodDeleteSerializer(serializers.Serializer):
    """Soft-deletes (deactivates) a shipping method."""

    def save(self, **kwargs):
        method           = self.context['method']
        method.is_active = False
        method.save(update_fields=['is_active'])


class CalculateShippingCostSerializer(serializers.Serializer):
    """
    Calculates shipping cost for a given address using market shipping methods.
    POST /orders/shipping-methods/calculate/
    """
    market_id      = serializers.IntegerField()
    country        = serializers.CharField(max_length=100)
    state_province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code    = serializers.CharField(max_length=20,  required=False, allow_blank=True)

    def validate_market_id(self, value):
        from apps.stores.models import Market
        try:
            self._market = Market.objects.get(pk=value, is_active=True)
        except Market.DoesNotExist:
            raise serializers.ValidationError("Market not found.")
        return value

    def calculate(self) -> dict:
        methods = self._market.shipping_methods.filter(is_active=True)
        return {
            'market':  self._market.market_name,
            'options': ShippingMethodListSerializer(methods, many=True).data,
        }


# ═════════════════════════════════════════════════════════════════════════════
# ORDER SHIPPING
# ═════════════════════════════════════════════════════════════════════════════

class OrderShippingSerializer(serializers.ModelSerializer):
    """Full shipping record for an order."""
    method_name      = serializers.CharField(source='shipping_method.name', read_only=True)
    delivery_estimate = serializers.SerializerMethodField()

    class Meta:
        model  = OrderShipping
        fields = [
            'id', 'method_name', 'tracking_number', 'carrier',
            'shipped_at', 'estimated_delivery', 'delivered_at',
            'delivery_estimate', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_delivery_estimate(self, obj):
        m = obj.shipping_method
        if m.estimated_days_min and m.estimated_days_max:
            return f"{m.estimated_days_min}–{m.estimated_days_max} days"
        return None


class OrderShippingCreateSerializer(serializers.ModelSerializer):
    """
    Attaches shipping info to an order. Seller only.
    POST /orders/<order_number>/shipping/
    """

    class Meta:
        model  = OrderShipping
        fields = ['shipping_method', 'tracking_number', 'carrier', 'estimated_delivery']
        extra_kwargs = {'shipping_method': {'required': True}}

    def validate_shipping_method(self, value):
        order = self.context['order']
        if value.market_id != order.market_id:
            raise serializers.ValidationError("Shipping method does not belong to this order's market.")
        return value

    def validate(self, attrs):
        order = self.context['order']
        if hasattr(order, 'shipping'):
            raise serializers.ValidationError("Shipping info already exists for this order.")
        return attrs

    def create(self, validated_data):
        return OrderShipping.objects.create(order=self.context['order'], **validated_data)


class OrderShippingUpdateSerializer(serializers.ModelSerializer):
    """
    Updates tracking number and carrier. Seller only.
    PATCH /orders/<order_number>/shipping/
    """

    class Meta:
        model  = OrderShipping
        fields = ['tracking_number', 'carrier', 'estimated_delivery']
        extra_kwargs = {f: {'required': False} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class OrderShippingTrackingSerializer(serializers.ModelSerializer):
    """
    Detailed tracking view for the buyer.
    GET /orders/<order_number>/tracking/
    """
    method_name       = serializers.CharField(source='shipping_method.name',        read_only=True)
    method_cost       = serializers.DecimalField(source='shipping_method.cost', max_digits=10, decimal_places=2, read_only=True)
    delivery_estimate = serializers.SerializerMethodField()
    order_status      = serializers.CharField(source='order.status', read_only=True)
    order_number      = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model  = OrderShipping
        fields = [
            'order_number', 'order_status',
            'method_name', 'method_cost',
            'tracking_number', 'carrier',
            'shipped_at', 'estimated_delivery', 'delivered_at',
            'delivery_estimate',
        ]
        read_only_fields = fields

    def get_delivery_estimate(self, obj):
        m = obj.shipping_method
        if m.estimated_days_min and m.estimated_days_max:
            return f"{m.estimated_days_min}–{m.estimated_days_max} days"
        return None


class TrackingUpdateSerializer(serializers.Serializer):
    """
    Updates tracking number and optionally marks the order as shipped.
    PATCH /orders/<order_number>/shipping/tracking/
    """
    tracking_number = serializers.CharField(max_length=100)
    carrier         = serializers.CharField(max_length=100)
    mark_as_shipped = serializers.BooleanField(default=True)

    def save(self, **kwargs):
        shipping                 = self.context['shipping']
        shipping.tracking_number = self.validated_data['tracking_number']
        shipping.carrier         = self.validated_data['carrier']
        shipping.save()

        if self.validated_data['mark_as_shipped']:
            order = shipping.order
            if order.status == Order.CONFIRMED or order.status == Order.PROCESSING:
                order.status = Order.SHIPPED
                order.save(update_fields=['status', 'shipped_at'])

        return shipping


# ═════════════════════════════════════════════════════════════════════════════
# ORDERS
# ═════════════════════════════════════════════════════════════════════════════

class OrderSerializer(serializers.ModelSerializer):
    """Basic order info — used as a nested reference."""
    status_display         = serializers.CharField(source='get_status_display',         read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'total_amount', 'currency', 'created_at',
        ]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    """
    Minimal order row for listing pages — optimised for performance.
    """
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    item_count      = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_status', 'total_amount', 'currency',
            'item_count', 'created_at',
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.order_items.count()


class OrderBuyerListSerializer(serializers.ModelSerializer):
    """Buyer's order history — includes market name and thumbnail."""
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    market_name     = serializers.CharField(source='market.market_name', read_only=True)
    item_count      = serializers.SerializerMethodField()
    first_item_name = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_status', 'total_amount', 'currency',
            'market_name', 'item_count', 'first_item_name',
            'created_at',
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.order_items.count()

    def get_first_item_name(self, obj):
        item = obj.order_items.first()
        return item.product_name if item else None


class OrderSellerListSerializer(serializers.ModelSerializer):
    """Seller's fulfilment queue — buyer name, status, total."""
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    buyer_name      = serializers.SerializerMethodField()
    buyer_email     = serializers.EmailField(source='user.email', read_only=True)
    item_count      = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_status', 'total_amount', 'currency',
            'buyer_name', 'buyer_email', 'item_count',
            'created_at',
        ]
        read_only_fields = fields

    def get_buyer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_item_count(self, obj):
        return obj.order_items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Complete order — items, addresses, shipping, payment info.
    GET /orders/<order_number>/
    """
    status_display         = serializers.CharField(source='get_status_display',         read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    market_name            = serializers.CharField(source='market.market_name',         read_only=True)
    market_slug            = serializers.CharField(source='market.slug',                read_only=True)
    items                  = OrderItemDetailSerializer(source='order_items', many=True,  read_only=True)
    addresses              = OrderAddressSerializer(many=True,                           read_only=True)
    shipping               = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number',
            'status', 'status_display',
            'payment_status', 'payment_status_display',
            'subtotal', 'tax_amount', 'shipping_cost',
            'discount_amount', 'total_amount', 'currency',
            'notes',
            'market_name', 'market_slug',
            'items', 'addresses', 'shipping',
            'created_at', 'updated_at',
            'paid_at', 'shipped_at', 'delivered_at', 'cancelled_at',
        ]
        read_only_fields = fields

    def get_shipping(self, obj):
        try:
            return OrderShippingSerializer(obj.shipping).data
        except OrderShipping.DoesNotExist:
            return None


class OrderCreateSerializer(serializers.Serializer):
    """
    Creates a new order from the authenticated user's cart.
    POST /orders/checkout/

    Body:
      shipping_address_id  – UserAddress pk (shipping)
      billing_address_id   – UserAddress pk (billing, optional — defaults to shipping)
      shipping_method_id   – ShippingMethod pk
      notes                – customer notes (optional)
      coupon_code          – applied coupon code (optional)
    """
    shipping_address_id = serializers.IntegerField()
    billing_address_id  = serializers.IntegerField(required=False, allow_null=True)
    shipping_method_id  = serializers.IntegerField()
    notes               = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    coupon_code         = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_shipping_address_id(self, value):
        user = self.context['request'].user
        try:
            self._shipping_address = UserAddress.objects.get(pk=value, user=user)
        except UserAddress.DoesNotExist:
            raise serializers.ValidationError("Shipping address not found.")
        return value

    def validate_billing_address_id(self, value):
        if value is None:
            return value
        user = self.context['request'].user
        try:
            self._billing_address = UserAddress.objects.get(pk=value, user=user)
        except UserAddress.DoesNotExist:
            raise serializers.ValidationError("Billing address not found.")
        return value

    def validate_shipping_method_id(self, value):
        try:
            self._shipping_method = ShippingMethod.objects.get(pk=value, is_active=True)
        except ShippingMethod.DoesNotExist:
            raise serializers.ValidationError("Shipping method not found.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        try:
            cart = user.cart
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Your cart is empty.")

        if not cart.items.exists():
            raise serializers.ValidationError("Your cart is empty.")

        # All items must be from the same market
        market_ids = cart.items.values_list('product__market_id', flat=True).distinct()
        if market_ids.count() > 1:
            raise serializers.ValidationError(
                "All cart items must be from the same market. Please checkout one market at a time."
            )

        market = cart.items.first().product.market
        if self._shipping_method.market_id != market.pk:
            raise serializers.ValidationError(
                {"shipping_method_id": "Shipping method does not belong to this market."}
            )

        # Stock check
        for item in cart.items.select_related('product', 'variant').all():
            stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
            if item.quantity > stock:
                raise serializers.ValidationError(
                    f"Insufficient stock for '{item.product.name}'. Only {stock} unit(s) available."
                )

        # Optional coupon
        discount = Decimal('0.00')
        if attrs.get('coupon_code'):
            from apps.promotions.models import Coupon
            try:
                coupon = Coupon.objects.get(
                    code__iexact=attrs['coupon_code'],
                    is_active=True,
                    valid_from__lte=timezone.now(),
                    valid_until__gte=timezone.now(),
                    market=market,
                )
                subtotal = sum(i.total_price for i in cart.items.all())
                if coupon.discount_type == Coupon.PERCENTAGE:
                    discount = (subtotal * coupon.discount_value / 100).quantize(Decimal('0.01'))
                else:
                    discount = coupon.discount_value
                if coupon.max_discount_amount:
                    discount = min(discount, coupon.max_discount_amount)
                self._coupon   = coupon
                self._discount = discount
            except Exception:
                raise serializers.ValidationError({"coupon_code": "Invalid or expired coupon."})
        else:
            self._coupon   = None
            self._discount = Decimal('0.00')

        self._cart   = cart
        self._market = market
        return attrs

    @transaction.atomic
    def save(self, **kwargs) -> Order:
        request         = self.context['request']
        cart            = self._cart
        market          = self._market
        shipping_method = self._shipping_method
        discount        = self._discount

        # ── Compute totals ────────────────────────────────────────────────────
        subtotal  = sum(item.total_price for item in cart.items.all()).quantize(Decimal('0.01'))
        taxable   = max(subtotal - discount, Decimal('0.00'))
        tax       = (taxable * TAX_RATE).quantize(Decimal('0.01'))
        shipping  = shipping_method.cost.quantize(Decimal('0.01'))
        total     = (taxable + tax + shipping).quantize(Decimal('0.01'))

        # ── Capture IP ────────────────────────────────────────────────────────
        xff        = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')

        # ── Create Order ──────────────────────────────────────────────────────
        order = Order.objects.create(
            order_number    = _generate_order_number(),
            user            = request.user,
            market          = market,
            subtotal        = subtotal,
            tax_amount      = tax,
            shipping_cost   = shipping,
            discount_amount = discount,
            total_amount    = total,
            notes           = self.validated_data.get('notes', ''),
            ip_address      = ip_address,
            user_agent      = request.META.get('HTTP_USER_AGENT', ''),
        )

        # ── Create OrderItems + decrement stock ───────────────────────────────
        for item in cart.items.select_related('product', 'variant').all():
            OrderItem.objects.create(
                order        = order,
                product      = item.product,
                variant      = item.variant,
                product_name = item.product.name,
                variant_name = item.variant.variant_name if item.variant else None,
                sku          = item.variant.sku if item.variant else item.product.sku,
                quantity     = item.quantity,
                unit_price   = item.price,
            )
            # Decrement stock
            if item.variant:
                item.variant.__class__.objects.filter(pk=item.variant.pk).update(
                    stock_quantity=item.variant.stock_quantity - item.quantity
                )
            else:
                item.product.__class__.objects.filter(pk=item.product.pk).update(
                    stock_quantity=item.product.stock_quantity - item.quantity,
                    sold_count=item.product.sold_count + item.quantity,
                )

        # ── Create Addresses ──────────────────────────────────────────────────
        def _copy_address(user_address: UserAddress, addr_type: str):
            OrderAddress.objects.create(
                order          = order,
                address_type   = addr_type,
                full_name      = user_address.full_name,
                phone_number   = user_address.phone_number,
                address_line_1 = user_address.address_line_1,
                address_line_2 = user_address.address_line_2,
                city           = user_address.city,
                state_province = user_address.state_province,
                postal_code    = user_address.postal_code,
                country        = user_address.country,
            )

        _copy_address(self._shipping_address, OrderAddress.SHIPPING)
        billing = getattr(self, '_billing_address', self._shipping_address)
        _copy_address(billing, OrderAddress.BILLING)

        # ── Create OrderShipping ──────────────────────────────────────────────
        OrderShipping.objects.create(
            order           = order,
            shipping_method = shipping_method,
        )

        # ── Record coupon usage ───────────────────────────────────────────────
        if self._coupon:
            from apps.promotions.models import CouponUsage
            CouponUsage.objects.create(
                coupon          = self._coupon,
                order           = order,
                user            = request.user,
                discount_amount = discount,
            )
            self._coupon.usage_count += 1
            self._coupon.save(update_fields=['usage_count'])

        # ── Clear cart ────────────────────────────────────────────────────────
        cart.items.all().delete()

        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Updates limited order fields — buyer can only change notes before shipping.
    PATCH /orders/<order_number>/
    """

    class Meta:
        model  = Order
        fields = ['notes']

    def validate(self, attrs):
        order = self.instance
        if order.status not in CANCELLABLE_STATUSES:
            raise serializers.ValidationError("Order cannot be modified after it has shipped.")
        return attrs

    def update(self, instance, validated_data):
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save(update_fields=['notes'])
        return instance


class OrderDeleteSerializer(serializers.Serializer):
    """
    Cancels an order (alias for cancel — no hard delete).
    DELETE /orders/<order_number>/
    """
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        order = self.context['order']
        if order.status not in CANCELLABLE_STATUSES:
            raise serializers.ValidationError(
                f"Orders with status '{order.get_status_display()}' cannot be cancelled."
            )
        return attrs

    def save(self, **kwargs):
        order        = self.context['order']
        order.status = Order.CANCELLED
        order.notes  = self.validated_data.get('reason', '')
        order.save(update_fields=['status', 'notes', 'cancelled_at'])


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Updates the order status. Seller / admin only.
    PATCH /orders/<order_number>/status/
    """
    VALID_TRANSITIONS = {
        Order.ORDER_PENDING: [Order.CONFIRMED, Order.CANCELLED],
        Order.CONFIRMED:     [Order.PROCESSING, Order.CANCELLED],
        Order.PROCESSING:    [Order.SHIPPED,    Order.CANCELLED],
        Order.SHIPPED:       [Order.DELIVERED],
        Order.DELIVERED:     [],
        Order.CANCELLED:     [],
        Order.ORDER_REFUNDED:[],
    }

    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

    def validate_status(self, value):
        order           = self.context['order']
        allowed         = self.VALID_TRANSITIONS.get(order.status, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from '{order.get_status_display()}' to '{value}'. "
                f"Allowed: {allowed or 'none'}."
            )
        return value

    def save(self, **kwargs):
        order        = self.context['order']
        order.status = self.validated_data['status']
        order.save(update_fields=['status', 'shipped_at', 'delivered_at', 'cancelled_at'])
        return order


class OrderCancelSerializer(serializers.Serializer):
    """
    Cancels an order with an explicit reason field.
    POST /orders/<order_number>/cancel/
    """
    reason = serializers.CharField(required=True, min_length=10)

    def validate(self, attrs):
        order = self.context['order']
        user  = self.context['request'].user

        if order.status not in CANCELLABLE_STATUSES:
            raise serializers.ValidationError(
                f"Order cannot be cancelled. Current status: {order.get_status_display()}."
            )
        # Buyer can only cancel own orders; seller/admin can cancel any
        if not user.is_staff and order.market.seller_id != user.pk:
            if order.user_id != user.pk:
                raise serializers.ValidationError("You can only cancel your own orders.")
        return attrs

    def save(self, **kwargs):
        order             = self.context['order']
        order.status      = Order.CANCELLED
        order.admin_notes = self.validated_data['reason']
        order.save(update_fields=['status', 'admin_notes', 'cancelled_at'])
        return order


class OrderTrackingSerializer(serializers.Serializer):
    """
    Public-facing tracking summary for a buyer.
    GET /orders/<order_number>/track/
    """

    def to_representation(self, order: Order):
        shipping = None
        try:
            shipping = OrderShippingTrackingSerializer(order.shipping).data
        except OrderShipping.DoesNotExist:
            pass

        return {
            'order_number': order.order_number,
            'status':       order.status,
            'status_label': order.get_status_display(),
            'created_at':   order.created_at,
            'paid_at':      order.paid_at,
            'shipped_at':   order.shipped_at,
            'delivered_at': order.delivered_at,
            'cancelled_at': order.cancelled_at,
            'shipping':     shipping,
        }


class OrderHistorySerializer(serializers.ModelSerializer):
    """
    Order history with optional date range filter applied in the view.
    GET /orders/history/?from=YYYY-MM-DD&to=YYYY-MM-DD
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    market_name    = serializers.CharField(source='market.market_name', read_only=True)
    item_count     = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_status', 'total_amount', 'currency',
            'market_name', 'item_count', 'created_at',
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.order_items.count()


class OrderSearchSerializer(serializers.ModelSerializer):
    """
    Order search result row.
    GET /orders/search/?q=<order_number or product name>
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    market_name    = serializers.CharField(source='market.market_name', read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'total_amount', 'currency', 'market_name', 'created_at',
        ]
        read_only_fields = fields


class OrderStatsSerializer(serializers.Serializer):
    """
    Order analytics for buyer or seller dashboard.
    GET /orders/stats/
    """

    def to_representation(self, queryset):
        from django.db.models import Sum, Count
        agg = queryset.aggregate(
            total_orders   = Count('id'),
            total_spent    = Sum('total_amount'),
            total_items    = Sum('order_items__quantity'),
        )
        status_breakdown = {
            s: queryset.filter(status=s).count()
            for s, _ in Order.STATUS_CHOICES
        }
        return {
            'total_orders':      agg['total_orders']  or 0,
            'total_spent':       str(agg['total_spent'] or Decimal('0.00')),
            'total_items':       agg['total_items']   or 0,
            'status_breakdown':  status_breakdown,
        }


class OrderInvoiceSerializer(serializers.Serializer):
    """
    Generates a structured invoice / receipt for an order.
    GET /orders/<order_number>/invoice/
    """

    def to_representation(self, order: Order):
        shipping_address = order.addresses.filter(
            address_type=OrderAddress.SHIPPING
        ).first()
        billing_address  = order.addresses.filter(
            address_type=OrderAddress.BILLING
        ).first()

        return {
            'invoice_number': f"INV-{order.order_number}",
            'order_number':   order.order_number,
            'issued_at':      order.created_at,
            'paid_at':        order.paid_at,
            'seller': {
                'name':    order.market.market_name,
                'email':   order.market.business_email,
                'address': order.market.business_address,
            },
            'buyer': {
                'name':  order.user.get_full_name() or order.user.username,
                'email': order.user.email,
            },
            'shipping_address': OrderAddressSerializer(shipping_address).data if shipping_address else None,
            'billing_address':  OrderAddressSerializer(billing_address).data  if billing_address  else None,
            'items':            OrderItemSerializer(order.order_items.all(), many=True).data,
            'subtotal':         str(order.subtotal),
            'discount':         str(order.discount_amount),
            'tax':              str(order.tax_amount),
            'shipping':         str(order.shipping_cost),
            'total':            str(order.total_amount),
            'currency':         order.currency,
            'payment_status':   order.payment_status,
        }