"""
stores/urls.py
===============
Include in your project urls.py with:
  path('stores/', include('apps.stores.urls')),

Full URL map
─────────────────────────────────────────────────────────────────
MARKET CRUD
  GET     /stores/markets/                        list all active markets
  POST    /stores/markets/                        create market (auth)
  GET     /stores/markets/<pk>/                   public market detail
  PATCH   /stores/markets/<pk>/                   update market (owner)
  DELETE  /stores/markets/<pk>/                   deactivate market (owner)
  GET     /stores/markets/<pk>/detail/            full detail (owner/admin)
  GET     /stores/markets/slug/<slug>/            public detail by slug

SELLER'S OWN MARKET
  GET     /stores/my-market/                      seller management view
  GET     /stores/my-market/stats/                performance stats
  GET     /stores/my-market/settings/             view settings
  PATCH   /stores/my-market/settings/             update settings
  POST    /stores/my-market/verify/               request verification
  GET     /stores/my-market/analytics/            detailed analytics

DISCOVERY & SEARCH
  GET     /stores/markets/search/                 search markets (?q=)
  GET     /stores/markets/featured/               featured markets
  GET     /stores/markets/popular/                most popular markets
  GET     /stores/markets/browse/                 browse with filters
  GET     /stores/markets/by-category/<id>/       markets by category
  GET     /stores/markets/nearby/                 nearby markets (?address=)
  GET     /stores/markets/trending/               trending markets
  GET     /stores/markets/following/              markets user follows

REVIEWS
  GET     /stores/markets/<pk>/reviews/           list approved reviews
  POST    /stores/markets/<pk>/reviews/           create review (auth)
  GET     /stores/markets/<pk>/reviews/stats/     rating breakdown
  GET     /stores/markets/reviews/<pk>/           review detail
  PATCH   /stores/markets/reviews/<pk>/           edit own review
  DELETE  /stores/markets/reviews/<pk>/           delete own review

FOLLOWERS
  POST    /stores/markets/<pk>/follow/            follow market
  DELETE  /stores/markets/<pk>/follow/            unfollow market
  GET     /stores/markets/<pk>/followers/         list followers (owner)
─────────────────────────────────────────────────────────────────
"""


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
    
    

]






# urlpatterns = [

#     # ── Review detail (static segment 'reviews' before <pk>) ─────────────────
#     path('markets/reviews/<int:pk>/',           MarketReviewDetailView.as_view(), name='market-review-detail'),

#     # ── Reviews under a market ────────────────────────────────────────────────
#     path('markets/<int:pk>/reviews/',           MarketReviewListCreateView.as_view(), name='market-review-list'),
#     path('markets/<int:pk>/reviews/stats/',     MarketReviewStatsView.as_view(),      name='market-review-stats'),

#     # ── Followers ─────────────────────────────────────────────────────────────
#     path('markets/<int:pk>/follow/',            MarketFollowView.as_view(),       name='market-follow'),
#     path('markets/<int:pk>/followers/',         MarketFollowersListView.as_view(), name='market-followers'),
# ]