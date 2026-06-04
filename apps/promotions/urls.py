from django.urls import path
from .views import (
    CouponListCreateView, CouponDetailView, CouponStatsView,
    CouponPublicListView, CouponsActiveListView, CouponValidateView,
    CouponApplyView, CouponUsageLisView, CouponUsageStatsView,
    MyCouponUsageView, FlashSaleListCreateView, FlashSaleDetailView,
    DealOfTheDayView, ActiveDealsView, UpcomingDealsView, ExpiredDealsView,
    ClearanceSaleView, SeasonalSaleView, BundleDealsView,
    PromotionListCreateView, PromotionDetailView, PromotionStatsView,
    PromotionClickView, SellerPromotionListView,
)

urlpatterns = [
    # Coupons
    path('coupons/', CouponListCreateView.as_view(), name='coupon-list-create'),
    path('coupons/public/', CouponPublicListView.as_view(), name='coupon-public-list'),
    path('coupons/active/', CouponsActiveListView.as_view(), name='coupon-active-list'),
    path('coupons/validate/', CouponValidateView.as_view(), name='coupon-validate'),
    path('coupons/apply/', CouponApplyView.as_view(), name='coupon-apply'),
    path('coupons/usage/stats/', CouponUsageStatsView.as_view(), name='coupon-usage-stats'),
    path('coupons/<int:pk>/', CouponDetailView.as_view(), name='coupon-detail'),
    path('coupons/<int:pk>/stats/', CouponStatsView.as_view(), name='coupon-stats'),
    path('coupons/<int:pk>/usage/', CouponUsageLisView.as_view(), name='coupon-usage-list'),

    # Coupon usage (buyer)
    path('my-usage/', MyCouponUsageView.as_view(), name='my-coupon-usage'),

    # Flash sales
    path('flash-sales/', FlashSaleListCreateView.as_view(), name='flash-sale-list-create'),
    path('flash-sales/<int:pk>/', FlashSaleDetailView.as_view(), name='flash-sale-detail'),

    # Deal views
    path('deal-of-the-day/', DealOfTheDayView.as_view(), name='deal-of-the-day'),
    path('active/', ActiveDealsView.as_view(), name='active-deals'),
    path('upcoming/', UpcomingDealsView.as_view(), name='upcoming-deals'),
    path('expired/', ExpiredDealsView.as_view(), name='expired-deals'),
    path('clearance/', ClearanceSaleView.as_view(), name='clearance-sale'),
    path('seasonal/', SeasonalSaleView.as_view(), name='seasonal-sale'),
    path('bundles/', BundleDealsView.as_view(), name='bundle-deals'),

    # Promotions
    path('', PromotionListCreateView.as_view(), name='promotion-list-create'),
    path('my-promotions/', SellerPromotionListView.as_view(), name='seller-promotions'),
    path('<int:pk>/', PromotionDetailView.as_view(), name='promotion-detail'),
    path('<int:pk>/stats/', PromotionStatsView.as_view(), name='promotion-stats'),
    path('<int:pk>/click/', PromotionClickView.as_view(), name='promotion-click'),
]