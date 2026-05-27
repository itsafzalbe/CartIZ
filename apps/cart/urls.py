"""
cart/urls.py
=============
Include in your project urls.py with:
  path('cart/', include('apps.cart.urls')),

Full URL map
─────────────────────────────────────────────────────────────────
CART
  GET     /cart/                              basic cart + item list
  GET     /cart/detail/                       cart with full product details
  GET     /cart/summary/                      totals (subtotal, tax, shipping)
  GET     /cart/item-count/                   badge count

CART ITEMS — CRUD
  GET     /cart/items/                        list all items (minimal)
  POST    /cart/items/                        add item
  GET     /cart/items/<pk>/                   single item detail
  PATCH   /cart/items/<pk>/                   update quantity
  DELETE  /cart/items/<pk>/                   remove item

CART ITEMS — OPERATIONS
  POST    /cart/add/                          add to cart (main storefront)
  PATCH   /cart/items/<pk>/quantity/          set absolute quantity
  DELETE  /cart/clear/                        empty cart
  PATCH   /cart/items/bulk-update/            update multiple items
  DELETE  /cart/items/bulk-delete/            remove multiple items
  POST    /cart/items/<pk>/move-to-wishlist/  move item to wishlist
  POST    /cart/items/<pk>/save-for-later/    save item for later
  POST    /cart/move-from-wishlist/           move wishlist item to cart

CART OPERATIONS
  POST    /cart/coupon/apply/                 apply coupon code
  DELETE  /cart/coupon/                       remove applied coupon
  POST    /cart/shipping/calculate/           calculate shipping options
  POST    /cart/validate/                     validate cart before checkout
─────────────────────────────────────────────────────────────────
"""

from django.urls import path
from .views import *

urlpatterns = [

    # ── Cart ──────────────────────────────────────────────────────────────────
    path('',                    CartView.as_view(),          name='cart'),
    path('detail/',             CartDetailView.as_view(),    name='cart-detail'),
    path('summary/',            CartSummaryView.as_view(),   name='cart-summary'),
    path('item-count/',         CartItemCountView.as_view(), name='cart-item-count'),

    # ── Cart items — static paths before <pk> ────────────────────────────────
    path('items/bulk-update/',  CartItemBulkUpdateView.as_view(),  name='cart-items-bulk-update'),
    path('items/bulk-delete/',  CartItemBulkDeleteView.as_view(),  name='cart-items-bulk-delete'),
    path('items/',              CartItemListCreateView.as_view(),   name='cart-items'),
    path('items/<int:pk>/',                     CartItemDetailView.as_view(),      name='cart-item-detail'),
    path('items/<int:pk>/quantity/',            UpdateCartQuantityView.as_view(),  name='cart-item-quantity'),
    path('items/<int:pk>/move-to-wishlist/',    MoveToWishlistView.as_view(),      name='cart-item-move-to-wishlist'),
    path('items/<int:pk>/save-for-later/',      SaveForLaterView.as_view(),        name='cart-item-save-for-later'),

    # ── Cart-level operations ─────────────────────────────────────────────────
    path('add/',                    AddToCartView.as_view(),         name='cart-add'),
    path('clear/',                  ClearCartView.as_view(),         name='cart-clear'),
    path('move-from-wishlist/',     MoveToCartView.as_view(),        name='cart-move-from-wishlist'),

    # ── Coupon ────────────────────────────────────────────────────────────────
    path('coupon/apply/',   ApplyCouponView.as_view(),    name='cart-coupon-apply'),
    path('coupon/',         RemoveCouponView.as_view(),   name='cart-coupon-remove'),

    # ── Shipping & validation ─────────────────────────────────────────────────
    path('shipping/calculate/', CalculateShippingView.as_view(), name='cart-shipping-calculate'),
    path('validate/',           CartValidationView.as_view(),    name='cart-validate'),
]