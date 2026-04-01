# 9. STORES APP (31 serializers)
# Market/Store:
#
# MarketSerializer - Views basic market/store information
# MarketCreateSerializer - Creates new market/store (seller)
# MarketUpdateSerializer - Updates market details
# MarketDeleteSerializer - Deletes or deactivates market
# MarketDetailSerializer - Shows complete market with products and stats
# MarketListSerializer - Lists markets with minimal data
# MarketPublicSerializer - Shows market as buyers see it
# MarketSellerSerializer - Shows market from seller's management view
# MarketStatsSerializer - Returns market performance statistics
# MarketSearchSerializer - Returns market search results
# MarketSettingsSerializer - Manages market settings and preferences
# MarketVerificationSerializer - Handles market verification process
# MarketAnalyticsSerializer - Shows detailed market analytics
#
# Market Discovery:
#
# FeaturedMarketsSerializer - Returns featured/promoted markets
# PopularMarketsSerializer - Shows most popular markets
# MarketBrowseSerializer - Shows market browsing page with filters
# MarketCategorySerializer - Lists markets by category
# NearbyMarketsSerializer - Shows markets near user location
# TrendingMarketsSerializer - Returns currently trending markets
#
# Market Reviews:
#
# MarketReviewSerializer - Views market review details
# MarketReviewCreateSerializer - Creates new market review
# MarketReviewUpdateSerializer - Updates existing market review
# MarketReviewDeleteSerializer - Deletes market review
# MarketReviewListSerializer - Lists all reviews for a market
# MarketReviewStatsSerializer - Shows market rating breakdown
# MarketReviewDetailSerializer - Shows review with full user information
#
# Market Followers:
#
# MarketFollowerSerializer - Views market follower information
# FollowMarketSerializer - Follows a market to get updates
# UnfollowMarketSerializer - Unfollows a market
# MarketFollowersListSerializer - Lists all followers of a market
# FollowedMarketsSerializer - Lists markets user is following