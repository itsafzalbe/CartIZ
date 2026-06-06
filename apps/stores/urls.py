from django.urls import path
from .views import *

urlpatterns = [
    # ── Market CRUD ───────────────────────────────────────────────────────────
    path('markets/',                          MarketListView.as_view(),         name='market-list'),
    path('markets/<int:pk>/',                 MarketDetailView.as_view(),       name='market-detail'),
    path('markets/<int:pk>/detail/',          MarketFullDetailView.as_view(),   name='market-full-detail'),


    # ── Discovery (static segments → before <pk> patterns) ───────────────────
    path('markets/slug/<slug:slug>/',               MarketBySlugView.as_view(),       name='market-by-slug'),
    path('markets/search/',                         MarketSearchView.as_view(),       name='market-search'),
    path('markets/featured/',                       FeaturedMarketsView.as_view(),    name='market-featured'),
    path('markets/popular/',                        PopularMarketsView.as_view(),     name='market-popular'),
    path('markets/browse/',                         MarketBrowseView.as_view(),       name='market-browse'),
    path('markets/trending/',                       TrendinMarketsView.as_view(),     name='market-trending'),
    #path('markets/following/',                     FollowedMarketsView.as_view(),    name='market-following'),
    path('markets/by-category/<int:category_id>/', MarketByCategoryView.as_view(),    name='market-by-category'),




    # ── Seller's own market (specific → before generic) ───────────────────────
    path('my-market/',                MyMarketView.as_view(),           name='my-market'),
    path('my-market/stats/',          MarketStatsView.as_view(),        name='my-market-stats'),
    path('my-market/settings/',       MarketSettingsView.as_view(),     name='my-market-settings'),
    path('my-market/verify/',         MarketVerificationView.as_view(), name='my-market-verify'),
    path('my-market/analytics/',      MarketAnalyticsView.as_view(),    name='my-market-analytics'),

    # ── Review detail (static segment 'reviews' before <pk>) ─────────────────
    path('markets/reviews/<int:pk>/',       MarketReviewDetailView.as_view(),       name='market-review-detail'),


    # ── Reviews under a market ────────────────────────────────────────────────
    path('markets/<int:pk>/reviews/',       MarketReviewListCreateView.as_view(),   name='market-review-list'),
    path('markets/<int:pk>/reviews/stats/', MarketReviewStatsView.as_view(),        name='market-review-stats'),

    # ── Followers ─────────────────────────────────────────────────────────────
    # path('markets/<int:pk>/follow/',        MarketFollowView.as_view(),             name='market-follow'),
    # path('markets/<int:pk>/followers/',     MarketFollowersListView.as_view(),      name='market-followers'),

]