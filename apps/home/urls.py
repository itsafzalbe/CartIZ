from django.urls import path
from .views import *

urlpatterns = [

    # Homepage sections
    path('', HomepageView.as_view(), name='homepage'),
    path('hero/', HeroSectionView.as_view(), name='hero-section'),
    path('featured/', FeaturedSectionView.as_view(), name='featured-section'),
    path('trending/', TrendingSectionView.as_view(), name='trending-section'),
    path('deals/', DealsOfTheDayView.as_view(), name='deals-of-the-day'),

    # Banners — static paths before <pk>
    path('banners/promotional/', PromotionalBannersView.as_view(), name='banners-promotional'),
    path('banners/', BannerListView.as_view(), name='banner-list'),
    path('banners/<int:pk>/', BannerDetailView.as_view(), name='banner-detail'),
    path('banners/<int:pk>/click/', BannerClickView.as_view(), name='banner-click'),

    #  Newsletter & Contact 
    path('newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='newsletter-subscribe'),
    path('newsletter/unsubscribe/', NewsletterUnsubscribeView.as_view(), name='newsletter-unsubscribe'),
    path('contact/', ContactFormView.as_view(), name='contact-form'),

    # Navigation
    path('navigation/mega-menu/', MegaMenuView.as_view(), name='mega-menu'),
    path('navigation/categories/', NavigationCategoriesView.as_view(), name='nav-categories'),
    path('navigation/quick-links/', QuickLinksView.as_view(), name='quick-links'),
    path('navigation/footer/', FooterLinksView.as_view(), name='footer-links'),
    path('navigation/breadcrumb/', BreadcrumbView.as_view(), name='breadcrumb'),

    # Search — static paths before parameterised ones
    path('search/results/', SearchResultsView.as_view(), name='search-results'),
    path('search/suggestions/', SearchSuggestionsView.as_view(), name='search-suggestions'),
    path('search/popular/', PopularSearchesView.as_view(), name='search-popular'),
    path('search/filters/', SearchFiltersView.as_view(), name='search-filters'),
    path('search/history/<int:pk>/', SearchHistoryItemDeleteView.as_view(), name='search-history-item'),
    path('search/history/', SearchHistoryView.as_view(), name='search-history'),
    path('search/', GlobalSearchView.as_view(), name='global-search'),

    # Analytics
    path('analytics/page-view/', PageViewTrackView.as_view(),  name='analytics-page-view'),
    path('analytics/click/', ClickTrackingView.as_view(),  name='analytics-click'),
    path('analytics/activity/', UserActivityLogView.as_view(), name='analytics-activity'),
    path('analytics/event/', AnalyticsEventView.as_view(), name='analytics-event'),
]