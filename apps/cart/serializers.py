"""
cart/serializers.py
====================
Cart           (4)  CartSerializer, CartDetailSerializer,
                    CartSummarySerializer, CartItemCountSerializer
Cart Items     (14) CartItemSerializer, CartItemCreateSerializer,
                    CartItemUpdateSerializer, CartItemDeleteSerializer,
                    CartItemListSerializer, CartItemDetailSerializer,
                    AddToCartSerializer, UpdateCartQuantitySerializer,
                    ClearCartSerializer, CartItemBulkUpdateSerializer,
                    CartItemBulkDeleteSerializer, MoveToWishlistSerializer,
                    SaveForLaterSerializer, MoveToCartSerializer
Cart Operations(4)  ApplyCouponToCartSerializer, RemoveCouponFromCartSerializer,
                    CalculateShippingForCartSerializer, CartValidationSerializer
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.products.models import *
from .models import *

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

TAX_RATE = Decimal('0.12')      # 12% - tax rate
FREE_SHIP_ABOVE = Decimal('100.00')
BASE_SHIP_COST = Decimal('9.99') 

def _current_price(product: Product, variant: ProductVariant | None) -> Decimal:
    """Return the live price for a product or variant"""
    return variant.price if variant else product.price

def _get_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

def _validate_item_ownership(item: CartItem, user) -> None:
    if item.cart.user_id != user.pk:
        raise serializers.ValidationError("Cart item not found.")
    
# ═════════════════════════════════════════════════════════════════════════════
# CART
# ═════════════════════════════════════════════════════════════════════════════

class CartItemListSerializer(serializers.ModelSerializer):
    """Lightweight item - used inside CartSerializer."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    variant_name = serializers.SerializerMethodField()
    total_price = serializers.ReadOnlyField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product_name', 'product_slug',
            'variant_name', 'quantity', 'price', 'total_price',
            'primary_image', 'added_at',
        ]
        read_only_fields = fields
    
    def get_variant_name(self, obj):
        return obj.variant.variant_name if obj.variant else None
    
    def get_primary_image(self, obj):
        img = obj.product.product_images.filter(is_primary=True).first() \
            or obj.product.product_images.first()
        return img.image.url if img else None

# ─────────────────────────────────────────────────────────────────────────────
class CartSerializer(serializers.ModelSerializer):
    """
    Cart with basic item list
    GET /cart/
    """

    items = CartItemListSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'item_count', 'items', 'created_at', 'updated_at']
        read_only_fields = fields
    
    def get_item_count(self, obj):
        return obj.items.count()
    
# ─────────────────────────────────────────────────────────────────────────────
class CartItemDetailSerializer(serializers.ModelSerializer):
    """Full item with hydrated product and variant objects."""
    product = serializers.SerializerMethodField()
    variant = serializers.SerializerMethodField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'variant', 'quantity', 'price', 'total_price', 'added_at', 'updated_at']
        read_only_fields = fields
    
    def get_product(self, obj):
        from apps.products.serializers import ProductCardSerializer
        return ProductCardSerializer(obj.product).data

    def get_variant(self, obj):
        if not obj.variant:
            return None
        from apps.products.serializers import ProductVariantSerializer
        return ProductVariantSerializer(obj.variant).data

# ─────────────────────────────────────────────────────────────────────────────
class CartDetailSerializer(serializers.ModelSerializer):
    """
    Cart with full hydrated items
    GET /cart/detail/
    """

    items = CartItemDetailSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'item_count', 'items', 'updated_at']
        read_only_fields = fields
    
    def get_item_count(self, obj):
        return obj.items.count()

# ─────────────────────────────────────────────────────────────────────────────
class CartSummarySerializer(serializers.Serializer):
    """
    Cart totals - subtotal, tax, shipping, discount, grand total.
    GET /cart/summary/
    Coupon discount is injected by the view from sessions / applied coupon.
    """

    def to_representation(self, cart: Cart):
        items = cart.items.all()
        subtotal = sum(item.total_price for item in items)
        discount = self.context.get('discount', Decimal('0.00'))
        taxable = max(subtotal - discount, Decimal('0.00'))
        tax = (taxable * TAX_RATE).quantize(Decimal('0.01'))
        shipping = Decimal('0.00') if subtotal >= FREE_SHIP_ABOVE else BASE_SHIP_COST
        total = taxable + tax + shipping

        return {
            'item_count':           items.count(),
            'subtotal':             str(subtotal.quantize(Decimal('0.01'))),
            'discount':             str(discount.quantize(Decimal('0.01'))),
            'tax':                  str(tax),
            'tax_rate':             str(TAX_RATE),
            'shipping':             str(shipping),
            'free_ship_above':      str(FREE_SHIP_ABOVE),
            'total':                str(total.quantize(Decimal('0.01'))),
        }

# ─────────────────────────────────────────────────────────────────────────────
class CartItemCountSerializer(serializers.Serializer):
    """Item count for the cart badge in the headers."""
    def to_representation(self, cart: Cart):
        return {'item_count': cart.items.count()}
    

# ═════════════════════════════════════════════════════════════════════════════
# CART ITEMS
# ═════════════════════════════════════════════════════════════════════════════

class CartItemSerializer(serializers.ModelSerializer):
    """Single cart item - read-only view."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    variant_name = serializers.SerializerMethodField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product_name', 'product_slug',
            'variant_name', 'quantity', 'price', 'total_price',
            'added_at', 'updated_at',
        ]
        read_only_fields = fields
    
    def get_variant_name(self, obj):
        return obj.variant.variant_name if obj.variant else None
    
# ─────────────────────────────────────────────────────────────────────────────
class CartItemCreateSerializer(serializers.ModelSerializer):
    """
    Adds an item to the cart with quantity and availability validation.
    POST /cart/items/
    If the item already exists the quantity is incremented.
    """
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = CartItem
        fields = ['product_id', 'variant_id', 'quantity']
        extra_kwargs = {'quantity': {'default': 1}}
    
    def validate(self, attrs):
        try:
            product = Product.objects.get(pk=attrs['product_id'], is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found or unavailable."})
        
        variant = None
        if attrs.get('variant_id'):
            try:
                variant = ProductVariant.objects.get(pk=attrs['variant_id'], product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError({"variant_id": "Variant not found or unavailable"})
        
        stock = variant.stock_quantity if variant else product.stock_quantity
        if stock < attrs['quantity']:
            raise serializers.ValidationError(
                f"Only {stock} unit(s) available."
            )
        
        attrs['_product'] = product
        attrs['_variant'] = variant
        return attrs
    
    @transaction.atomic
    def save(self):
        cart = _get_cart(self.context['request'].user)
        product = self.validated_data['_product']
        variant = self.validated_data['_variant']
        qty = self.validated_data['quantity']
        price = _current_price(product, variant)

        if variant:
            item, created = CartItem.objects.get_or_create(
                cart=cart, variant=variant, 
                defaults={'product': product, 'quantity': qty, 'price': price},
            )
        else:
            item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, variant=None,
                defaults={'quantity': qty, 'price': price}
            )
        if not created:
            new_qty = item.quantity + qty
            stock = variant.stock_quantity if variant else product.stock_quantity
            if new_qty > stock:
                raise serializers.ValidationError(
                    f"Cannot add {qty} more. Only {stock - item.quantity} additional unit(s) available"
                )
            item.quantity = new_qty
            item.price = price
            item.save()
        
        return item
    
# ─────────────────────────────────────────────────────────────────────────────
class CartItemUpdateSerializer(serializers.ModelSerializer):
    """
    Updates the quantity of an existing cart item
    PATCH /cart/items/<id>/
    """

    class Meta:
        model = CartItem
        fields = ['quantity']
    
    def validate_quantity(self, value):
        item = self.instance
        stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
        if value > stock:
            raise serializers.ValidationError(f"Only {stock} unit(s) available")
        return value
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data['quantity']
        instance.save(update_fields=['quantity'])
        return instance

# ─────────────────────────────────────────────────────────────────────────────
class CartItemDeleteSerializer(serializers.Serializer):
    """Removes a single item from the cart."""

    def save(self):
        self.context['item'].delete()

# ─────────────────────────────────────────────────────────────────────────────
class AddToCartSerializer(serializers.Serializer):
    """
    Richer add-to-cart with explicit stock validation and price snapshot
    POST /cart/add/
    Preferred over CartItemCreateSerializer for the main storefront button
    """
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        try:
            product = Product.objects.get(pk=attrs['product_id'], is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found"})
        
        variant = None
        if attrs.get('variant'):
            try:
                variant = ProductVariant.objects.get(
                    pk=attrs['variant_id'], product=product, is_active=True
                )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError({"variant_id": "Variant not found"})
        
        stock = variant.stock_quantity if variant else product.stock_quantity
        if stock == 0:
            raise serializers.ValidationError("This item is out of stock")
        if attrs['quantity'] > stock:
            raise serializers.ValidationError(f"Only {stock} unit(s) in stock")
        
        attrs['_product'] = product
        attrs['_variant'] = variant
        return attrs
    
    @transaction.atomic
    def save(self):
        cart = _get_cart(self.context['request'].user)
        product = self.validated_data['_product']
        variant = self.validated_data['_variant']
        qty = self.validated_data['quantity']
        price = _current_price(product, variant)

        if variant:
            item, created = CartItem.objects.get_or_create(
                cart=cart, variant=variant,
                defaults={'product': product, 'quantity': qty, 'price': price},
            )
        else:
            item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, variant=None,
                defaults={'quantity': qty, 'price': price},
            )
        
        if not created:
            stock = variant.stock_quantity if variant else product.stock_quantity
            new_qty = item.quantity + qty
            if new_qty > stock:
                raise serializers.ValidationError(f"Only {stock - item.quantity} more unit(s) can be added.")
            item.quantity = new_qty
            item.price = price
            item.save()
    
        return item

# ─────────────────────────────────────────────────────────────────────────────
class UpdateCartQuantitySerializer(serializers.Serializer):
    """
    Sets an absolute quantity on a cart item.
    PATCH /cart/items/<id>/quantity/
    """

    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        item = self.context['item']
        stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
        if value > stock:
            raise serializers.ValidationError(f"Only {stock} unti(s) available.")
        return value
    
    def save(self):
        item = self.context['item']
        item.quantity = self.validated_data['quantity']
        item.save(update_fields=['quantity'])
        return item

# ─────────────────────────────────────────────────────────────────────────────
class ClearCartSerializer(serializers.Serializer):
    """
    Removes all items from the cart
    DELETE /cart/clear/
    """

    def save(self):
        cart = _get_cart(self.context['request'].user)
        cart.items.all().delete()

# ─────────────────────────────────────────────────────────────────────────────
class CartItemBulkUpdateSerializer(serializers.Serializer):
    """
    Updates multiple cart item in one request.
    PATCH /cart/items/bulk-update/
    Body: { "updates": [{ "id": 1, "quantity": 3 }, ...] }"""

    class _ItemUpdate(serializers.Serializer):
        id = serializers.IntegerField()
        quantity = serializers.IntegerField(min_value=1)
    
    updates = serializers.ListField(child=_ItemUpdate(), min_length=1)

    def validate_updates(self, value):
        cart = _get_cart(self.context['request'].user)
        ids = [u['id'] for u in value]
        items_qs = cart.items.filter(pk__in=ids)
        found = {item.pk: item for item in items_qs}

        missing = set(ids) - set(found.keys())
        if missing:
            raise serializers.ValidationError(f"Items not found: {list(missing)}")
        
        errors = []
        for update in value:
            item = found[update['id']]
            stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
            if update['quantity'] > stock:
                errors.append(f"Item {item.id}: only {stock} unit(s) available.")
        if errors:
            raise serializers.ValidationError(errors)
        
        self._items = found
        return value
    
    @transaction.atomic
    def save(self):
        for update in self.validated_data['updates']:
            item = self._items[update['id']]
            item.quantity = update['quantity']
            item.save(update_fields=['quantity'])
        return list(self._items.values())

# ─────────────────────────────────────────────────────────────────────────────
class CartItemBulkDeleteSerializer(serializers.Serializer):
    """
    Removes multiple items from the cart
    DELETE /cart/items/bulk-delete/
    Body: { "item_ids": [1, 2, 3] }
    """
    item_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)

    def validate_item_ids(self, value):
        cart = _get_cart(self.context['request'].user)
        found = set(cart.items.filter(pk__in=value).values_list('pk', flat=True))
        missing = set(value) - found
        if missing:
            raise serializers.ValidationError(f"Items not found: {list(missing)}")
        return value
    
    def save(self):
        cart = _get_cart(self.context['request'].user)
        cart.items.filter(pk__in=self.validated_data['item_ids']).delete()

# ─────────────────────────────────────────────────────────────────────────────
class MoveToWishlistSerializer(serializers.Serializer):
    """
    Moves a cart to a wishlist and removes it from the cart.
    POST /cart/items/<id>/move-to-wishlist/
    """
    wishlist_id = serializers.IntegerField()

    def validate(self, attrs):
        user = self.context['request'].user
        item = self.context['item']
        _validate_item_ownership(item, user)

        try:
            wishlist = Wishlist.objects.get(pk=attrs['wishlist_id'], user=user)
        except Wishlist.DoesNotExist:
            raise serializers.ValidationError({"wishlist_id": "Wishlist not found."})
        
        if item.variant:
            if wishlist.items.filter(variant=item.variant).exists():
                raise serializers.ValidationError("This variant is already in the wishlist.")
        else:
            if wishlist.items.filter(product=item.product, variant__isnull=True).exists():
                raise serializers.ValidationError("This product is already in the wishlist.")
        
        attrs['_wishlist'] = wishlist
        return attrs
    
    @transaction.atomic
    def save(self):
        item = self.context['item']
        wishlist = self.validated_data['_wishlist']
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=item.product,
            variant=item.variant,
        )
        item.delete()

# ─────────────────────────────────────────────────────────────────────────────
class SaveForLaterSerializer(serializers.Serializer):
    """
    Saves a cart item for later (moves to a saved for later wishlist)
    POST /cart/items/<id>/save-for-later/
    Auto-creates a saved for later wishlist if one doesnt exist
    """

    def validate(self, attrs):
        user = self.context['request'].user
        item = self.context['item']
        _validate_item_ownership(item, user)
        return attrs
    
    @transaction.atomic
    def save(self):
        user = self.context['request'].user
        item = self.context['item']

        wishlist, _ = Wishlist.objects.get_or_create(user=user, name='Saved for Later', defaults={'is_public': False})

        if item.variant:
            exists = wishlist.items.filter(variant=item.variant).exists()
        else:
            exists = wishlist.items.filter(product=item.product, variant__isnull=True).exists()
        
        if not exists:
            WishlistItem.objects.create(
                wishlist=wishlist,
                product=item.product,
                variant=item.variant,
            )
        item.delete()
        return wishlist

# ─────────────────────────────────────────────────────────────────────────────
class MoveToCartSerializer(serializers.Serializer):
    """
    Moves a wishlist item to the cart
    POST /cart/move-from-wishlist/
    Body: { "wishlist_item_id": <id>, "quantity": 1 }
    """

    wishlist_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        user = self.context['request'].user
        try: 
            wl_item = WishlistItem.objects.select_related(
                'product', 'variant', 'wishlist'
            ).get(pk=attrs['wishlist_item_id'], wishlist__user=user)
        except WishlistItem.DoesNotExist:
            raise serializers.ValidationError({"wishlist_item_id": "Wishlist item not found."})
        
        product = wl_item.product
        variant = wl_item.variant

        if not product.is_active:
            raise serializers.ValidationError("This product is no longer available.")

        stock = variant.stock_quantity if variant else product.stock_quantity
        if attrs['quantity'] > stock:
            raise serializers.ValidationError(f"Only {stock} unit(s) available.")
        
        attrs['_wl_item'] = wl_item
        attrs['_product'] = product
        attrs['_variant'] = variant
        return attrs
    
    @transaction.atomic
    def save(self):
        user = self.context['request'].user
        wl_item = self.validated_data['_wl_item']
        product = self.validated_data['_product']
        variant = self.validated_data['_variant']
        qty = self.validated_data['quantity']
        price = _current_price(product, variant)

        cart = _get_cart(user)

        if variant:
            item, created = CartItem.objects.get_or_create(
                cart=cart, variant=variant,
                defaults={'product': product, 'quantity': qty, 'price': price},
            )
        else:
            item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, variant=None,
                defaults={'quantity': qty, 'price': price},
            )
        if not created:
            item.quantity += qty
            item.price = price
            item.save()
        
        wl_item.delet()
        return item


# ═════════════════════════════════════════════════════════════════════════════
# CART OPERATIONS
# ═════════════════════════════════════════════════════════════════════════════
class ApplyCouponToCartSerializer(serializers.Serializer):
    """
    Validates and applies a coupon to the cart.
    POST /cart/coupon/apply/
    Stores the applied coupon in the session (view handles session write)
    """
    code = serializers.CharField(max_length=50)

    def validate_code(self, value):
        from apps.promotions.models import Coupon
        from django.utils import timezone

        try:
            coupon = Coupon.objects.get(
                code__iexact=value,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
            )
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired coupon code.")
        
        # Usage limit check 
        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            raise serializers.ValidationError("This coupon has reached its usage limit.")
        
        #per -user limit
        user = self.context['request'].user
        user_usage = coupon.usage.filter(user=user).count()
        if user_usage >= coupon.per_user_limit:
            raise serializers.ValidationError("You have already used this coupon the maximum number of times.")
        
        self._coupon = coupon
        return value
    
    def calculate_discount(self) -> Decimal:
        """Call aftr is_valid() to get the discount amount for the cart."""
        from apps.promotions.models import Coupon
        coupon = self._coupon
        cart = _get_cart(self.context['request'].user)
        subtotal = sum(item.total_price for item in cart.items.all())

        if coupon.min_purchase_amount and subtotal < coupon.min_purchase_amount:
            raise serializers.ValidationError(
                f"Minimum order of {coupon.min_purchase_amount} required for this coupon"
            )
        
        if coupon.discount_type == Coupon.PERCENTAGE:
            discount = (subtotal * coupon.discount_value / 100).quantize(Decimal('0.01'))
        else:
            discount = coupon.discount_value
        
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
        
        return discount
    
    def get_coupon(self):
        return self._coupon

# ─────────────────────────────────────────────────────────────────────────────
class RemoveCouponFromCartSerializer(serializers.Serializer):
    """
    Removes the applied coupon from the cart session
    DELETE /cart/coupon/
    The view clears the session key: this seraializer just validates the request.
    """

    def validate(self, attrs):
        if not self.context.get('has_coupon'):
            raise serializers.ValidationError("No coupon is currently applied.")
        return attrs
    
    def save(self):
        pass # view clears the session key after calling save()

# ─────────────────────────────────────────────────────────────────────────────
class CalculateShippingForCartSerializer(serializers.Serializer):
    """
    Calculates estimated shipping cost for the cart given an address.
    POST /cart/shipping/calculate/
    """
    country = serializers.CharField(max_length=100)
    state_province  = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code     = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def calculate(self) -> dict:
        """
        Returns shipping options
        """
        cart = _get_cart(self.context['request'].user)
        subtotal = sum(item.total_price for item in cart.items.all())

        if subtotal >= FREE_SHIP_ABOVE:
            return {
                'options': [
                    {'name': 'Free Shipping', 'cost': '0.00', 'estimated_days': '5-7'},
                ]
            }
        return {
            'options': [
                {'name': 'Standard Shipping', 'cost': str(BASE_SHIP_COST), 'estimated_days': '5-7'},
                {'name': 'Express Shipping',  'cost': '19.99',              'estimated_days': '2-3'},
                {'name': 'Overnight',         'cost': '34.99',              'estimated_days': '1'},
            ]
        }


# ─────────────────────────────────────────────────────────────────────────────
class CartValidationSerializer(serializers.Serializer):
    """
    Vlaidates the entire cart before checkout:
        -product still active
        - sufficient stock
        - price hasnt changed more than 10%
    POST /cart/validate/
    Returns a list of issues; empty list = cart is valid
    """

    def validate_cart(self) -> list:
        cart = _get_cart(self.context['request'].user)
        issues = []

        for item in cart.items.select_related('product', 'variant').all():
            product = item.product
            variant = item.variant

            if not product.is_active:
                issues.append({
                    'item_id':  item.pk,
                    'type':     'unavailable',
                    'message':  f"'{product.name}' is no longer available.",
                })
                continue
            if variant and not variant.is_active:
                issues.append({
                    'item_id': item.pk,
                    'type':    'unavailable',
                    'message': f"The selected variant of '{product.name}' is no longer available.",
                })
                continue
            stock = variant.stock_quantity if variant else product.stock_quantity
            if item.quantity > stock:
                issues.append({
                    'item_id':   item.pk,
                    'type':      'stock',
                    'message':   f"Only {stock} unit(s) of '{product.name}' available.",
                    'available': stock,
                })
            
            live_price = _current_price(product, variant)
            if item.price != live_price:
                pct_change = abs(live_price - item.price) / item.price * 100
                if pct_change > 10:
                    issues.append({
                        'item_id':    item.pk,
                        'type':       'price_change',
                        'message':    f"Price of '{product.name}' has changed.",
                        'old_price':  str(item.price),
                        'new_price':  str(live_price),
                    })
                # Always sync price
                item.price = live_price
                item.save(update_fields=['price'])
        
        return issues









