"""
cart/views.py
==============
All views require IsAuthenticated.
Session key CART_COUPON stores { "code": ..., "discount": ... }.
"""
from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .serializers import *
from apps.utils.response_helpers import *
CART_COUPON_KEY = 'cart_coupon'


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────
def _get_or_create_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

def _get_cart_item(cart: Cart, item_id: int) -> CartItem | None:
    try:
        return cart.items.get(pk=item_id)
    except CartItem.DoesNotExist:
        return None

def _session_discount(request) -> Decimal:
    coupon_data = request.session.get(CART_COUPON_KEY)
    if coupon_data:
        try:
            return Decimal(coupon_data['discount'])
        except (KeyError, Exception):
            pass
    return Decimal('0.00')

# ═════════════════════════════════════════════════════════════════════════════
# CART
# ═════════════════════════════════════════════════════════════════════════════
class CartView(APIView):
    """
    GET /cart/ -> basic cart with item list
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        return ok("Cart retrieved.", data=CartSerializer(cart).data)
    
class CartDetailView(APIView):
    """
    GET /cart/detail - cart with full product details per item
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        return ok("Cart detail retrieved.", data=CartDetailSerializer(cart).data)

class CartSummaryView(APIView):
    """
    GET /cart/summary/ -> subtotal, tax, shipping, discount, total
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        discount = _session_discount(request)
        data = CartSummarySerializer(
            cart, 
            context={"request": request, "discount": discount},
        ).data
        return ok("Cart summary retrieved.", data=data)

class CartItemCountView(APIView):
    """
    GET /cart/item-count/       -> {item_count: N} for header badge
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        return ok("Item count retrieved.", data=CartItemCountSerializer(cart).data)
    

# ═════════════════════════════════════════════════════════════════════════════
# CART ITEMS — CRUD
# ═════════════════════════════════════════════════════════════════════════════
class CartItemListCreateView(APIView):
    """
    GET /cart/items/        -> list all items (minimal)
    POST /cart/items/       -> add item to cart
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        items = cart.items.all()
        from .serializers import CartItemListSerializer
        return ok("Cart items retrieved.", data={
            "count": items.count(),
            "items": CartItemListSerializer(items, many=True).data,
        })
    
    def post(self, request):
        s = CartItemCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        item = s.save()
        return created("Item added to cart.", data=CartItemSerializer(item).data)

class CartItemDetailView(APIView):
    """
    GET     /cart/items/<pk>/   -> single item detail
    PATCH   /cart/items/<pk>/   -> upate quantity
    DELETE  /cart/items/<pk>/   -> removes item
    """

    permission_classes = [IsAuthenticated]

    def _get_item(self, request, pk):
        cart = _get_or_create_cart(request.user)
        item = _get_cart_item(cart, pk)
        if not item:
            return None
        return item

    def get(self, request, pk):
        item = self._get_item(request, pk)
        if not item:
            return not_found("Cart item not found.")
        return ok("Cart item retrieved.", data=CartItemSerializer(item).data)
    
    def patch(self, request, pk):
        item = self._get_item(request, pk)
        if not item:
            return not_found("Cart item not found.")
        s = CartItemUpdateSerializer(item, data=request.data)
        s.is_valid(raise_exception=True)
        return ok("Cart item updated.", data=CartItemSerializer(s.save()).data)
    
    def delete(self, request, pk):
        item = self._get_item(request, pk)
        if not item:
            return not_found("Cart item not found.")
        CartItemDeleteSerializer(data={}, context={"item": item}).save()
        return ok("Item removed from the cart.")

# ═════════════════════════════════════════════════════════════════════════════
# CART ITEMS — DEDICATED OPERATIONS
# ═════════════════════════════════════════════════════════════════════════════
class AddToCartView(APIView):
    """
    POST /cart/add/
    Main storefront add-to-cart with full stock validation
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = AddToCartSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        item = s.save()
        return created("Item added to cart.", data=CartItemSerializer(item).data)
    
class UpdateCartQuantityView(APIView):
    """
    PATCH /cart/add/
    Main storefront add-to-cart with full stock validation.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = AddToCartSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        item = s.save()
        return created("Item added to cart.", data=CartItemSerializer(item).data)

class UpdateCartQuantityView(APIView):
    """
    PATCH /cart/items/<pk>/quantity/
    Absolute quantity seter (replaces current quantity)
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        cart = _get_or_create_cart(request.user)
        item = _get_cart_item(cart, pk)
        if not item:
            return not_found("Cart item not found.")
        s = UpdateCartQuantitySerializer(
            data=request.data, context={"request": request, "item": item},
        )
        s.is_valid(raise_exception=True)
        return ok("Quantity updated.", data=CartItemSerializer(s.save()).data)

class ClearCartView(APIView):
    """
    DELETE /cart/clear/
    Removes all items from the cart
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        s = ClearCartSerializer(data={}, context={"request": request})
        s.is_valid(raise_exception=True)
        s.save()
        request.session.pop(CART_COUPON_KEY, None)
        return ok("Cart cleared.")

class CartItemBulkUpdateView(APIView):
    """
    PATCH /cart/items/bulk-update/
    Body: { "updates": [{ "id": 1, "quantity": 3 }, ...] }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        s = CartItemBulkUpdateSerializer(
            data=request.data,
            context={"request": request},
        )
        s.is_valid(raise_exception=True)
        items = s.save()
        from .serializers import CartItemListSerializer
        return ok(f"{len(items)} item(s) updated.", data={
            "items": CartItemListSerializer(items, many=True).data
        })


class CartItemBulkDeleteView(APIView):
    """
    DELETE /cart/items/bulk-delete/
    Body: { "item_ids": [1, 2, 3] }
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        s = CartItemBulkDeleteSerializer(
            data=request.data, context={"request": request}
        )
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Items removed from cart.")

class MoveToWishlistView(APIView):
    """
    POST /cart/items/<pk>/move-to-wishlist/
    Body: { "wishlist_id": <id> }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        cart = _get_or_create_cart(request.user)
        item = _get_cart_item(cart, pk)
        if not item:
            return not_found("Cart item not found.")
        s = MoveToWishlistSerializer(
            data=request.data,
            context={"request": request, "item": item},
        )
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Item moved to wishlist")


class SaveForLaterView(APIView):
    """
    POST /cart/items/<pk>/save-for-later/
    Moves item to auto-created 'Saved for Later' wishlist.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        cart = _get_or_create_cart(request.user)
        item = _get_cart_item(cart, pk)
        if not item:
            return not_found("Cart item not found.")
        s = SaveForLaterSerializer(
            data={}, context={"request": request, "item": item},
        )
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Item saved for later.")

class MoveToCartView(APIView):
    """
    POST /cart/move-from-wishlist/
    Body: { "wishlist_item_id": <id>, "quantity": 1 }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = MoveToCartSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        item = s.save()
        return created("Item moved to cart.", data=CartItemSerializer(item).data)


# ═════════════════════════════════════════════════════════════════════════════
# CART OPERATIONS
# ═════════════════════════════════════════════════════════════════════════════
class ApplyCouponView(APIView):
    """
    POST /cart/coupon/apply/
    Body: { "code": "SAVE20" }
    Stores coupon + discount in the session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ApplyCouponToCartSerializer(
            data=request.data,
            context={"request": request},
        )
        s.is_valid(raise_exception=True)

        try:
            discount = s.calculate_discount()
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        coupon = s.get_coupon()
        request.session[CART_COUPON_KEY] = {
            "code": coupon.code,
            "discount": str(discount),
        }

        cart = _get_or_create_cart(request.user)
        summary = CartSummarySerializer(
            cart, context={"request": request, "discount": discount}
        ).data

        return ok("Coupon applied.", data={
            "coupon_code": coupon.code,
            "discount":    str(discount),
            "summary":     summary,
        })

class RemoveCouponView(APIView):
    """
    DELETE /cart/coupon/
    Removes the applied coupon from the session
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        has_coupon = CART_COUPON_KEY in request.session
        s = RemoveCouponFromCartSerializer(
            data={},
            context={"request": request, "has_coupon": has_coupon},
        )
        s.is_valid(raise_exception=True)
        request.session.pop(CART_COUPON_KEY, None)
        return ok("Coupon removed.")

class CalculateShippingView(APIView):
    """
    POST /cart/shipping/calculate/
    Body: { "country": "US", "state_province": "CA", "postal_code": "90210" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CalculateShippingForCartSerializer(
            data=request.data,
            context={"request": request},
        )
        s.is_valid(raise_exception=True)
        options = s.calculate()
        return ok("Shipping options calculated.", data=self.options)

class CartValidationView(APIView):
    """
    POST /cart/validate/
    Validates the cart before checkout.
    Returns { "valid": true, "issue": [] } or { "valid": false, "issues": [...] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CartValidationSerializer(data={}, context={"request": request})
        issues = s.validate_cart()
        valid = len(issues) == 0
        return ok(
            "Cart is valid." if valid else "Cart has issues that need to be resolved.",
            data={"valid": valid, "issues": issues},
            http_status=status.HTTP_200_OK,
        )
