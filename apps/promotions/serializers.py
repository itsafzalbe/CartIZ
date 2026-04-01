# 8. PROMOTIONS APP (30 serializers)
# Coupons:
#
# CouponSerializer - Views coupon details
# CouponCreateSerializer - Creates new coupon code (seller/admin)
# CouponUpdateSerializer - Updates coupon details
# CouponDeleteSerializer - Deletes or deactivates coupon
# CouponListSerializer - Lists all coupons with filters
# CouponDetailSerializer - Shows complete coupon information
# CouponValidateSerializer - Validates coupon code at checkout
# CouponApplySerializer - Applies coupon to cart/order
# CouponPublicSerializer - Shows publicly available coupons
# CouponStatsSerializer - Returns coupon usage statistics
# CouponActiveSerializer - Lists currently active coupons
#
# Coupon Usage:
#
# CouponUsageSerializer - Views coupon usage record
# CouponUsageListSerializer - Lists all coupon usage history
# CouponUsageStatsSerializer - Shows coupon usage analytics
#
# Deals & Sales:
#
# DealOfTheDaySerializer - Shows current deal of the day
# FlashSaleSerializer - Views flash sale details
# FlashSaleCreateSerializer - Creates new flash sale
# FlashSaleUpdateSerializer - Updates flash sale details
# ClearanceSaleSerializer - Shows clearance/discount items
# SeasonalSaleSerializer - Shows seasonal promotions
# BundleDealsSerializer - Returns bundle/combo deals
# ActiveDealsSerializer - Lists all currently active deals
# UpcomingDealsSerializer - Shows upcoming scheduled deals
# ExpiredDealsSerializer - Lists past/expired deals
#
# Promotions:
#
# PromotionSerializer - Views promotion details
# PromotionCreateSerializer - Creates new promotion campaign
# PromotionUpdateSerializer - Updates promotion details
# PromotionListSerializer - Lists all promotions
# PromotionDetailSerializer - Shows complete promotion information
# PromotionStatsSerializer - Returns promotion performance statistics