"""
orders/urls.py
===============
Include in your project urls.py with:
  path('orders/', include('apps.orders.urls')),

Full URL map
─────────────────────────────────────────────────────────────────
CHECKOUT
  POST    /orders/checkout/                               create order from cart

ORDER LIST & SEARCH
  GET     /orders/                                        list orders (role-based)
  GET     /orders/my-orders/                              buyer's own orders
  GET     /orders/seller-orders/                          seller's fulfilment queue
  GET     /orders/history/                                order history (?from=&to=)
  GET     /orders/search/                                 search orders (?q=)
  GET     /orders/stats/                                  aggregated stats

ORDER DETAIL
  GET     /orders/<order_number>/                         full order detail
  PATCH   /orders/<order_number>/                         update notes (buyer)
  DELETE  /orders/<order_number>/                         cancel order (buyer)
  POST    /orders/<order_number>/cancel/                  cancel with reason
  PATCH   /orders/<order_number>/status/                  update status (seller/admin)
  GET     /orders/<order_number>/track/                   buyer tracking page
  GET     /orders/<order_number>/invoice/                 invoice / receipt

ORDER ITEMS
  GET     /orders/<order_number>/items/                   list items in order
  GET     /orders/<order_number>/items/<item_id>/         single item detail

ORDER ADDRESSES
  GET     /orders/<order_number>/addresses/               both addresses
  GET     /orders/<order_number>/addresses/shipping/      shipping address only
  GET     /orders/<order_number>/addresses/billing/       billing address only

ORDER SHIPPING
  GET     /orders/<order_number>/shipping/                shipping details
  POST    /orders/<order_number>/shipping/                attach shipping (seller)
  PATCH   /orders/<order_number>/shipping/                update tracking (seller)
  GET     /orders/<order_number>/shipping/tracking/       detailed tracking view
  PATCH   /orders/<order_number>/shipping/tracking/update/ update tracking number

SHIPPING METHODS
  GET     /orders/shipping-methods/                       list methods (?market_id=)
  POST    /orders/shipping-methods/                       create method (seller)
  POST    /orders/shipping-methods/calculate/             calculate cost for address
  GET     /orders/shipping-methods/<pk>/                  method detail
  PATCH   /orders/shipping-methods/<pk>/                  update method (seller)
  DELETE  /orders/shipping-methods/<pk>/                  deactivate method (seller)
─────────────────────────────────────────────────────────────────
"""

from django.urls import path

from .views import (
    # Checkout
    CheckoutView,
    # Order lists
    OrderListView,
    BuyerOrderListView,
    SellerOrderListView,
    OrderHistoryView,
    OrderSearchView,
    OrderStatsView,
    # Order detail & actions
    OrderDetailView,
    OrderCancelView,
    OrderStatusUpdateView,
    OrderTrackingView,
    OrderInvoiceView,
    # Order items
    OrderItemListView,
    OrderItemDetailView,
    # Order addresses
    OrderAddressView,
    OrderShippingAddressView,
    OrderBillingAddressView,
    # Order shipping
    OrderShippingView,
    OrderTrackingDetailView,
    TrackingUpdateView,
    # Shipping methods
    ShippingMethodListCreateView,
    ShippingMethodDetailView,
    CalculateShippingCostView,
)

urlpatterns = [

    # ── Checkout ──────────────────────────────────────────────────────────────
    path('checkout/', CheckoutView.as_view(), name='order-checkout'),

    # ── Order lists — static paths before <order_number> ─────────────────────
    path('my-orders/',      BuyerOrderListView.as_view(),  name='my-orders'),
    path('seller-orders/',  SellerOrderListView.as_view(), name='seller-orders'),
    path('history/',        OrderHistoryView.as_view(),    name='order-history'),
    path('search/',         OrderSearchView.as_view(),     name='order-search'),
    path('stats/',          OrderStatsView.as_view(),      name='order-stats'),

    # ── Shipping methods — static paths before <order_number> ─────────────────
    path('shipping-methods/calculate/',     CalculateShippingCostView.as_view(),    name='shipping-cost-calculate'),
    path('shipping-methods/',               ShippingMethodListCreateView.as_view(), name='shipping-method-list'),
    path('shipping-methods/<int:pk>/',      ShippingMethodDetailView.as_view(),     name='shipping-method-detail'),

    # ── Order list (admin / default) ──────────────────────────────────────────
    path('', OrderListView.as_view(), name='order-list'),

    # ── Order detail — <order_number> based ──────────────────────────────────
    # Important: static sub-paths (cancel, status, track, invoice, items,
    # addresses, shipping) must be defined before the bare <order_number>/
    # route only matters here because we're using str not slug, but keeping
    # them explicit is safer and more readable.

    path('<str:order_number>/cancel/',   OrderCancelView.as_view(),       name='order-cancel'),
    path('<str:order_number>/status/',   OrderStatusUpdateView.as_view(),  name='order-status-update'),
    path('<str:order_number>/track/',    OrderTrackingView.as_view(),      name='order-track'),
    path('<str:order_number>/invoice/',  OrderInvoiceView.as_view(),       name='order-invoice'),

    # ── Order items ───────────────────────────────────────────────────────────
    path('<str:order_number>/items/',                   OrderItemListView.as_view(),   name='order-items'),
    path('<str:order_number>/items/<int:item_id>/',     OrderItemDetailView.as_view(), name='order-item-detail'),

    # ── Order addresses ───────────────────────────────────────────────────────
    path('<str:order_number>/addresses/',            OrderAddressView.as_view(),         name='order-addresses'),
    path('<str:order_number>/addresses/shipping/',   OrderShippingAddressView.as_view(), name='order-address-shipping'),
    path('<str:order_number>/addresses/billing/',    OrderBillingAddressView.as_view(),  name='order-address-billing'),

    # ── Order shipping ────────────────────────────────────────────────────────
    # tracking/update must come before tracking/ to avoid prefix conflict
    path('<str:order_number>/shipping/tracking/update/', TrackingUpdateView.as_view(),      name='order-tracking-update'),
    path('<str:order_number>/shipping/tracking/',        OrderTrackingDetailView.as_view(), name='order-tracking-detail'),
    path('<str:order_number>/shipping/',                 OrderShippingView.as_view(),       name='order-shipping'),

    # ── Bare order detail — last to avoid shadowing sub-paths ────────────────
    path('<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
]