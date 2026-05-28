"""
orders/views.py
================
Permissions:
  IsAuthenticated  – all order views require login
  IsSellerOnly     – seller-specific views (status update, seller list)
  IsAdminUser      – admin-only operations
  IsBuyerOrSeller  – buyer owns the order OR seller owns the market
"""

from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderAddress, OrderItem, OrderShipping, ShippingMethod
from .serializers import (
    CalculateShippingCostSerializer,
    OrderBuyerListSerializer,
    OrderCancelSerializer,
    OrderCreateSerializer,
    OrderDeleteSerializer,
    OrderDetailSerializer,
    OrderHistorySerializer,
    OrderInvoiceSerializer,
    OrderItemDetailSerializer,
    OrderItemListSerializer,
    OrderItemSerializer,
    OrderListSerializer,
    OrderSearchSerializer,
    OrderSellerListSerializer,
    OrderSerializer,
    OrderShippingCreateSerializer,
    OrderShippingSerializer,
    OrderShippingTrackingSerializer,
    OrderShippingUpdateSerializer,
    OrderStatsSerializer,
    OrderStatusUpdateSerializer,
    OrderTrackingSerializer,
    OrderUpdateSerializer,
    ShippingMethodCreateSerializer,
    ShippingMethodDeleteSerializer,
    ShippingMethodListSerializer,
    ShippingMethodSerializer,
    ShippingMethodUpdateSerializer,
    TrackingUpdateSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────────────────────────────────────

def ok(message, data=None, http_status=status.HTTP_200_OK):
    body = {"status": "success", "message": message}
    if data is not None:
        body["data"] = data
    return Response(body, status=http_status)


def created(message, data=None):
    return ok(message, data, http_status=status.HTTP_201_CREATED)


def not_found(message="Not found."):
    return Response(
        {"status": "error", "message": message},
        status=status.HTTP_404_NOT_FOUND,
    )


def forbidden(message="Permission denied."):
    return Response(
        {"status": "error", "message": message},
        status=status.HTTP_403_FORBIDDEN,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Custom permissions
# ─────────────────────────────────────────────────────────────────────────────

class IsSellerOnly(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_seller


# ─────────────────────────────────────────────────────────────────────────────
# Shared lookup helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_buyer_order(order_number: str, user) -> Order | None:
    """Return an order that belongs to the buyer, or None."""
    try:
        return Order.objects.get(order_number=order_number, user=user)
    except Order.DoesNotExist:
        return None


def _get_seller_order(order_number: str, user) -> Order | None:
    """Return an order for the seller's market, or None."""
    try:
        return Order.objects.get(order_number=order_number, market__seller=user)
    except Order.DoesNotExist:
        return None


def _get_order_any(order_number: str, user) -> Order | None:
    """Return an order visible to buyer, seller, or staff."""
    try:
        return Order.objects.get(
            Q(order_number=order_number) &
            (Q(user=user) | Q(market__seller=user))
        )
    except Order.DoesNotExist:
        return None


# ═════════════════════════════════════════════════════════════════════════════
# CHECKOUT
# ═════════════════════════════════════════════════════════════════════════════

class CheckoutView(APIView):
    """
    POST /orders/checkout/
    Creates a new order from the user's cart.

    Body:
      shipping_address_id, billing_address_id (optional),
      shipping_method_id, notes (optional), coupon_code (optional)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return created(
            "Order placed successfully.",
            data=OrderDetailSerializer(order, context={"request": request}).data,
        )


# ═════════════════════════════════════════════════════════════════════════════
# ORDER LIST & DETAIL
# ═════════════════════════════════════════════════════════════════════════════

class OrderListView(APIView):
    """
    GET /orders/
    Admin: all orders.
    Seller: own market's orders.
    Buyer: own orders.
    Supports ?status=, ?payment_status= query filters.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_staff:
            qs = Order.objects.all()
        elif user.is_seller:
            qs = Order.objects.filter(market__seller=user)
        else:
            qs = Order.objects.filter(user=user)

        # Optional filters
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        payment_filter = request.query_params.get('payment_status')
        if payment_filter:
            qs = qs.filter(payment_status=payment_filter)

        qs = qs.order_by('-created_at')

        serializer = OrderListSerializer(qs, many=True)
        return ok("Orders retrieved.", data={"count": qs.count(), "orders": serializer.data})


class OrderDetailView(APIView):
    """
    GET    /orders/<order_number>/    → full order detail
    PATCH  /orders/<order_number>/    → update notes (buyer, before shipping)
    DELETE /orders/<order_number>/    → cancel order (buyer)
    """
    permission_classes = [IsAuthenticated]

    def _get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order and request.user.is_staff:
            try:
                order = Order.objects.get(order_number=order_number)
            except Order.DoesNotExist:
                pass
        return order

    def get(self, request, order_number):
        order = self._get(request, order_number)
        if not order:
            return not_found("Order not found.")
        return ok("Order retrieved.", data=OrderDetailSerializer(order).data)

    def patch(self, request, order_number):
        order = _get_buyer_order(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        serializer = OrderUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return ok("Order updated.", data=OrderSerializer(serializer.save()).data)

    def delete(self, request, order_number):
        order = _get_buyer_order(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        serializer = OrderDeleteSerializer(
            data=request.data,
            context={"order": order, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok("Order cancelled.")


# ═════════════════════════════════════════════════════════════════════════════
# BUYER VIEWS
# ═════════════════════════════════════════════════════════════════════════════

class BuyerOrderListView(APIView):
    """
    GET /orders/my-orders/
    Buyer's own order history with optional status filter.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Order.objects.filter(user=request.user).order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return ok("Your orders retrieved.", data={
            "count":  qs.count(),
            "orders": OrderBuyerListSerializer(qs, many=True).data,
        })


class OrderHistoryView(APIView):
    """
    GET /orders/history/
    Buyer's order history with optional date range.
    ?from=YYYY-MM-DD&to=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Order.objects.filter(user=request.user).order_by('-created_at')

        date_from = request.query_params.get('from')
        date_to   = request.query_params.get('to')

        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                qs = qs.filter(created_at__date__gte=parsed)

        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                qs = qs.filter(created_at__date__lte=parsed)

        return ok("Order history retrieved.", data={
            "count":  qs.count(),
            "orders": OrderHistorySerializer(qs, many=True).data,
        })


class OrderTrackingView(APIView):
    """
    GET /orders/<order_number>/track/
    Buyer-facing tracking page — no auth required for public tracking links.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_buyer_order(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        return ok("Tracking info retrieved.", data=OrderTrackingSerializer(order).data)


class OrderInvoiceView(APIView):
    """
    GET /orders/<order_number>/invoice/
    Returns structured invoice data for the buyer.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        return ok("Invoice retrieved.", data=OrderInvoiceSerializer(order).data)


class OrderCancelView(APIView):
    """
    POST /orders/<order_number>/cancel/
    Body: { "reason": "..." }
    Buyer cancels own order; seller can cancel their market's orders.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        serializer = OrderCancelSerializer(
            data=request.data,
            context={"order": order, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok("Order cancelled.")


# ═════════════════════════════════════════════════════════════════════════════
# SELLER VIEWS
# ═════════════════════════════════════════════════════════════════════════════

class SellerOrderListView(APIView):
    """
    GET /orders/seller-orders/
    Seller's fulfilment queue with optional status filter.
    """
    permission_classes = [IsSellerOnly]

    def get(self, request):
        qs = Order.objects.filter(market__seller=request.user).order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return ok("Seller orders retrieved.", data={
            "count":  qs.count(),
            "orders": OrderSellerListSerializer(qs, many=True).data,
        })


class OrderStatusUpdateView(APIView):
    """
    PATCH /orders/<order_number>/status/
    Body: { "status": "confirmed" }
    Seller or admin only — enforces valid status transitions.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_number):
        user = request.user
        if user.is_staff:
            order = get_object_or_404(Order, order_number=order_number)
        else:
            order = _get_seller_order(order_number, user)
            if not order:
                return not_found("Order not found.")

        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={"order": order, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return ok(
            f"Order status updated to '{order.get_status_display()}'.",
            data=OrderSerializer(order).data,
        )


# ═════════════════════════════════════════════════════════════════════════════
# ORDER SEARCH & STATS
# ═════════════════════════════════════════════════════════════════════════════

class OrderSearchView(APIView):
    """
    GET /orders/search/?q=<query>
    Searches by order number or product name within orders visible to the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response(
                {"status": "error", "message": "Search query is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if user.is_staff:
            qs = Order.objects.all()
        elif user.is_seller:
            qs = Order.objects.filter(market__seller=user)
        else:
            qs = Order.objects.filter(user=user)

        qs = qs.filter(
            Q(order_number__icontains=q) |
            Q(order_items__product_name__icontains=q) |
            Q(order_items__sku__icontains=q)
        ).distinct().order_by('-created_at')

        return ok(f"Search results for '{q}'.", data={
            "count":  qs.count(),
            "orders": OrderSearchSerializer(qs, many=True).data,
        })


class OrderStatsView(APIView):
    """
    GET /orders/stats/
    Returns aggregated stats for the current user (buyer or seller).
    Seller sees stats for their market orders.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            qs = Order.objects.all()
        elif user.is_seller:
            qs = Order.objects.filter(market__seller=user)
        else:
            qs = Order.objects.filter(user=user)

        return ok("Stats retrieved.", data=OrderStatsSerializer(qs).data)


# ═════════════════════════════════════════════════════════════════════════════
# ORDER ITEMS
# ═════════════════════════════════════════════════════════════════════════════

class OrderItemListView(APIView):
    """
    GET /orders/<order_number>/items/
    Lists all items in an order.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        items = order.order_items.all()
        return ok("Order items retrieved.", data={
            "count": items.count(),
            "items": OrderItemListSerializer(items, many=True).data,
        })


class OrderItemDetailView(APIView):
    """
    GET /orders/<order_number>/items/<item_id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number, item_id):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        item = get_object_or_404(OrderItem, pk=item_id, order=order)
        return ok("Order item retrieved.", data=OrderItemDetailSerializer(item).data)


# ═════════════════════════════════════════════════════════════════════════════
# ORDER ADDRESSES
# ═════════════════════════════════════════════════════════════════════════════

class OrderAddressView(APIView):
    """
    GET /orders/<order_number>/addresses/
    Returns both shipping and billing addresses.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        from .serializers import OrderAddressSerializer
        addresses = order.addresses.all()
        return ok("Addresses retrieved.", data={
            "addresses": OrderAddressSerializer(addresses, many=True).data,
        })


class OrderShippingAddressView(APIView):
    """
    GET /orders/<order_number>/addresses/shipping/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        address = order.addresses.filter(address_type=OrderAddress.SHIPPING).first()
        if not address:
            return not_found("Shipping address not found.")
        from .serializers import OrderShippingAddressSerializer
        return ok("Shipping address retrieved.", data=OrderShippingAddressSerializer(address).data)


class OrderBillingAddressView(APIView):
    """
    GET /orders/<order_number>/addresses/billing/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        address = order.addresses.filter(address_type=OrderAddress.BILLING).first()
        if not address:
            return not_found("Billing address not found.")
        from .serializers import OrderBillingAddressSerializer
        return ok("Billing address retrieved.", data=OrderBillingAddressSerializer(address).data)


# ═════════════════════════════════════════════════════════════════════════════
# ORDER SHIPPING
# ═════════════════════════════════════════════════════════════════════════════

class OrderShippingView(APIView):
    """
    GET   /orders/<order_number>/shipping/        → shipping details
    POST  /orders/<order_number>/shipping/        → attach shipping (seller)
    PATCH /orders/<order_number>/shipping/        → update tracking (seller)
    """
    permission_classes = [IsAuthenticated]

    def _get_order(self, request, order_number):
        user = request.user
        if user.is_staff:
            try:
                return Order.objects.get(order_number=order_number)
            except Order.DoesNotExist:
                return None
        return _get_order_any(order_number, user)

    def get(self, request, order_number):
        order = self._get_order(request, order_number)
        if not order:
            return not_found("Order not found.")
        try:
            return ok("Shipping details retrieved.", data=OrderShippingSerializer(order.shipping).data)
        except OrderShipping.DoesNotExist:
            return not_found("Shipping info not set yet.")

    def post(self, request, order_number):
        order = _get_seller_order(order_number, request.user)
        if not order and request.user.is_staff:
            try:
                order = Order.objects.get(order_number=order_number)
            except Order.DoesNotExist:
                pass
        if not order:
            return not_found("Order not found.")

        serializer = OrderShippingCreateSerializer(
            data=request.data,
            context={"order": order, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        shipping = serializer.save()
        return created("Shipping info added.", data=OrderShippingSerializer(shipping).data)

    def patch(self, request, order_number):
        order = _get_seller_order(order_number, request.user)
        if not order and request.user.is_staff:
            try:
                order = Order.objects.get(order_number=order_number)
            except Order.DoesNotExist:
                pass
        if not order:
            return not_found("Order not found.")
        try:
            shipping = order.shipping
        except OrderShipping.DoesNotExist:
            return not_found("Shipping info not set yet.")

        serializer = OrderShippingUpdateSerializer(shipping, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return ok("Shipping updated.", data=OrderShippingSerializer(serializer.save()).data)


class OrderTrackingDetailView(APIView):
    """
    GET /orders/<order_number>/shipping/tracking/
    Detailed tracking view for buyer.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = _get_order_any(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        try:
            return ok("Tracking details retrieved.", data=OrderShippingTrackingSerializer(order.shipping).data)
        except OrderShipping.DoesNotExist:
            return not_found("Tracking info not available yet.")


class TrackingUpdateView(APIView):
    """
    PATCH /orders/<order_number>/shipping/tracking/update/
    Seller updates tracking number and optionally marks order as shipped.
    Body: { "tracking_number": "...", "carrier": "...", "mark_as_shipped": true }
    """
    permission_classes = [IsSellerOnly]

    def patch(self, request, order_number):
        order = _get_seller_order(order_number, request.user)
        if not order:
            return not_found("Order not found.")
        try:
            shipping = order.shipping
        except OrderShipping.DoesNotExist:
            return not_found("Shipping info not set yet.")

        serializer = TrackingUpdateSerializer(
            data=request.data,
            context={"shipping": shipping, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        shipping = serializer.save()
        return ok("Tracking updated.", data=OrderShippingSerializer(shipping).data)


# ═════════════════════════════════════════════════════════════════════════════
# SHIPPING METHODS
# ═════════════════════════════════════════════════════════════════════════════

class ShippingMethodListCreateView(APIView):
    """
    GET  /orders/shipping-methods/               → list active methods for a market
    POST /orders/shipping-methods/               → create method (seller)
    ?market_id=<id>  required for GET
    """

    def get_permissions(self):
        return [IsSellerOnly()] if self.request.method == 'POST' else [IsAuthenticated()]

    def get(self, request):
        market_id = request.query_params.get('market_id')
        if not market_id:
            return Response(
                {"status": "error", "message": "market_id query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        methods = ShippingMethod.objects.filter(market_id=market_id, is_active=True)
        return ok("Shipping methods retrieved.", data={
            "count":   methods.count(),
            "methods": ShippingMethodListSerializer(methods, many=True).data,
        })

    def post(self, request):
        serializer = ShippingMethodCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        method = serializer.save()
        return created("Shipping method created.", data=ShippingMethodSerializer(method).data)


class ShippingMethodDetailView(APIView):
    """
    GET    /orders/shipping-methods/<pk>/    → full detail
    PATCH  /orders/shipping-methods/<pk>/    → update (seller who owns it)
    DELETE /orders/shipping-methods/<pk>/    → deactivate (seller who owns it)
    """
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        return get_object_or_404(ShippingMethod, pk=pk)

    def _assert_owner(self, method, user):
        if not user.is_staff and method.market.seller_id != user.pk:
            return False
        return True

    def get(self, request, pk):
        return ok("Shipping method retrieved.", data=ShippingMethodSerializer(self._get(pk)).data)

    def patch(self, request, pk):
        method = self._get(pk)
        if not self._assert_owner(method, request.user):
            return forbidden()
        serializer = ShippingMethodUpdateSerializer(method, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return ok("Shipping method updated.", data=ShippingMethodSerializer(serializer.save()).data)

    def delete(self, request, pk):
        method = self._get(pk)
        if not self._assert_owner(method, request.user):
            return forbidden()
        ShippingMethodDeleteSerializer(data={}, context={"method": method}).save()
        return ok("Shipping method deactivated.")


class CalculateShippingCostView(APIView):
    """
    POST /orders/shipping-methods/calculate/
    Body: { "market_id": 1, "country": "US", ... }
    Returns available shipping options for the given market + address.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CalculateShippingCostSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return ok("Shipping options calculated.", data=serializer.calculate())