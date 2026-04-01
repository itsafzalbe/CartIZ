# 4. HOME APP (25 serializers - No Models)
# Homepage/Dashboard:
#
# HomepageDataSerializer - Aggregates all homepage sections (banners, featured products, deals)
# BannerSerializer - Shows single homepage banner/slider image
# BannerListSerializer - Lists all active homepage banners
# PromotionalBannerSerializer - Shows promotional banner with link
# FeaturedSectionSerializer - Returns featured products section data
# HeroSectionSerializer - Shows hero section content
# TrendingSectionSerializer - Returns trending products section
# DealsOfTheDaySerializer - Shows daily deals section
# NewsletterSubscribeSerializer - Handles newsletter subscription
# ContactFormSerializer - Processes contact form submissions
#
# Navigation:
#
# MegaMenuSerializer - Returns complete mega menu structure with categories
# NavigationCategoriesSerializer - Shows categories for main navigation
# QuickLinksSerializer - Returns quick access links in header/footer
# FooterLinksSerializer - Shows footer navigation links
# BreadcrumbSerializer - Generates breadcrumb navigation trail
#
# Global Search:
#
# GlobalSearchSerializer - Searches across products, markets, and categories
# SearchResultsSerializer - Returns unified search results with filters
# SearchSuggestionsSerializer - Provides autocomplete search suggestions
# SearchHistorySerializer - Shows user's recent searches
# PopularSearchesSerializer - Returns trending search terms
# SearchFiltersSerializer - Shows available filters for search results
#
# Analytics & Tracking:
#
# PageViewSerializer - Tracks page views for analytics
# ClickTrackingSerializer - Tracks user clicks on products/banners
# UserActivityLogSerializer - Logs user activity for analytics
# AnalyticsEventSerializer - Records custom analytics events