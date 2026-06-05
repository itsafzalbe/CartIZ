from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .models import Banner, PopularSearch, SearchHistory
from .serializers import *

from apps.utils.response_helpers import *
from apps.utils.response_helpers import *


#HOMEPAGE
class HomepageView(APIView):
    """
    GET /home/
    Master homepage endpoint - returns every section in one call
    Cahsed for 5 minutes; personalized sections use the auth user when present
    """

    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 5))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        data = HomepageDataSerializer(user).data
        return ok("Homepage data retrieved,", data=data)

class HeroSectionView(APIView):
    """
    GET /home/hero/
    Hero banners + platform stats. Cache - firendly standalone endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        data = HeroSectionSerializer(None).data
        return ok("Hero section retrieved.", data=data)

class FeaturedSectionView(APIView):
    """
    GET /home/featured/
    Featured products - personalized for authenticated users.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        data = FeaturedSectionSerializer(user).data
        return ok("Feautred section retrieved.", data=data)
    

class TrendingSectionView(APIView):
    """
    GET /home/trending/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        data = TrendingSectionSerializer(None).data
        return ok("Trending section retrieved.", data=data)

class DealsOfTheDayView(APIView):
    """
    GET /home/deals/
    Live flesh sales and top discount promotions.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        data = DealsOfTheDaySerializer(None).data
        return ok("Deals of the day retrieved.", data=data)




#BANNERS
class BannerListView(APIView):
    """
    GET /home/banners/
    All active banners, optionally filtered by type.
    ?type=hero|slider|promotional|category
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Banner.objects.filter(is_active=True)
        banner_type = request.query_params.get('type')
        if banner_type:
            qs = qs.filter(banner_type=banner_type)
        live = [b for b in qs.order_by('position') if b.is_live]
        return ok("Banners retrieved.", data={
            "count": len(live),
            "banners": BannerListSerializer(live, many=True).data
        })

class BannerDetailView(APIView):
    """
    GET /home/banners/<pk>/
    Single banner detail.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        from django.shortcuts import get_object_or_404
        banner = get_object_or_404(Banner=Banner, pk=pk, is_active=True)
        return ok("Banner retrieved.", data=BannerSerializer(banner).data)
    

class PromotionalBannersView(APIView):
    """
    GET /home/banners/promotional/
    Promotional strip banners.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        banners = [
            b for b in Banner.objects.filter(
                banner_type=Banner.PROMOTIONAL, is_active=True
            ).order_by('position')[:6]
            if b.is_live
        ]
        return ok("Promotional banners retrieved.", data={
            "banners": PromotionalBannerSerializer(banners, many=True).data,
        })

class BannerClickView(APIView):
    """
    POST /home/banners/<pk>/click/
    Increments banner click count (fire-and-forget).
    """
    permission_classes = [AllowAny]

    def post(self, request, pk):
        Banner.objects.filter(pk=pk).update(
            click_count=Banner.objects.filter(pk=pk).values_list('click_count', flat=True).first() + 1
        )
        return ok("Click recorded")






# NEWSLETTER & CONTACT
class NewsletterSubscribeView(APIView):
    """
    POST /home/newsletter/subscribe/
    Body:  { "email": "...", "name": "...", "source": "footer" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = NewsletterSubscribeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return created("You have been subscribed to our newsletter.")

class NewsletterUnsubscribeView(APIView):
    """
    POST /home/newsletter/unsubscribe/
    Body: { "email": "..." }
    """ 
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        if not email:
            return Response(
                {"status": "error", "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .models import NewsletterSubscriber
        sub = NewsletterSubscriber.objects.filter(email=email, is_active=True).first()
        if sub:
            sub.is_active = False
            sub.unsubscribed_at = timezone.now()
            sub.save(update_fields=['is_active', 'unsubscribed_at'])
        #always returns 200 to prevent email enueration.
        return ok("You have been unsubscribed.")

class ContactFormView(APIView):
    """
    POST /home/contact/
    Body: { "name", "email", "subject", "message" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = ContactFormSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        s.save()
        return created(
            "Your message has been retrieved. We'll get back to you within 24 hours."
        )

#NAVIGATION
class MegaMenuView(APIView):
    """
    GET /home/navigation/mega-menu/
    Full mega-menu with categories, subcategories, and featured products.
    Cached for 10 minutes
    """
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 10))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        data = MegaMenuSerializer(None).data
        return ok("Mega menu retrieved.", data=data)
    

class NavigationCategoriesView(APIView):
    """
    GET /home/navigation/categories/
    Top-level categories for the main nav bar.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.products.models import Category
        cats = Category.objects.filter(
            is_active=True, parent_id__isnull=True
        ).order_by('order_position')[:12]
        return ok("Navigation categories retrieved.", data={
            "categories": NavigationCategoriesSerializer(cats, many=True).data,
        })

class QuickLinksView(APIView):
    """
    GET /home/navigation/quick-links/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return ok("Quick links retrieved.", data=QuickLinksSerializer(None).data)

class FooterLinksView(APIView):
    """
    GET /home/navigation/footer/"""
    permission_classes = [AllowAny]

    def get(self, request):
        return ok("Footer links retrieved.", data=FooterLinksSerializer(None).data)

class BreadcrumbView(APIView):
    """
    GET /home/navigation/breadcrumb/?path=/products/categories/5/
    Generates navigation breadcrumb from a URL path
    """
    permission_classes = [AllowAny]

    def get(self, request):
        path = request.query_params.get('path', '/')
        s = BreadcrumbSerializer(data={'path': path})
        s.is_valid(raise_exception=True)
        return ok("Breadcrumb retrieved.", data={"breadcrumb": s.build()})



#GLOBAL SEARCH
class GlobalSearchView(APIView):
    """
    GET /home/search/
    ?q=...&type=all|products|markets|categories&limit=5
    Searches across products, markets, categories simultaneously.
    Records search history for authenticated users.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        s = GlobalSearchSerializer(data=request.query_params)
        if not s.is_valid():
            return Response(
                {"status": "error", "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        results = s.search(user=request.user)
        return ok("Search results retrieved.", data=results)

class SearchResultsView(APIView):
    """
    GET /home/search/results/
    Full search results page with filtering and sorting.
    ?q=...&category=&min_price=&max_price=&min_rating=&in_stock=&sort=
    """
    permission_classes = [AllowAny]

    def get(self, request):
        s = SearchResultsSerializer(data=request.query_params)
        if not s.is_valid():
            return Response(
                {"status": "error", "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        results = s.get_results()
        return ok("Search results retrieved.", data=results)


class SearchSuggestionsView(APIView):
    """
    GET /home/search/suggestions/?q=...
    Autocomplete suggestions - product name + popular searches.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        s = SearchSuggestionsSerializer(data=request.query_params)
        if not s.is_valid():
            return Response(
                {"status": "error", "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        return ok("Suggestions retrieved.", data=s.suggest())


class SearchHistoryView(APIView):
    """
    GET    /home/search/history/    -> user's recent searches
    DELETE /home/search/history/    -> clear all history
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = SearchHistory.objects.filter(user=request.user).order_by('-searched_at')[:20]
        return ok("Search history retrieved.", data={
            "history": SearchHistorySerializer(history, many=True).data,
        })
    
    def delete(self, request):
        SearchHistory.objects.filter(user=request.user).delete()
        return ok("Search history cleared.")

class SearchHistoryItemDeleteView(APIView):
    """DELETE /home/search/history/<pk>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        SearchHistory.objects.filter(pk=pk, user=request.user).delete()
        return ok("Search history item removed.")

class PopularSearchesView(APIView):
    """
    GET /home/search/popular/
    Globally trending search terms.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        popular = PopularSearch.objects.order_by('-count')[:15]
        return ok("Popular searches retrieved.", data={
            "searches": PopularSearchesSerializer(popular, many=True).data,
        })

class SearchFiltersView(APIView):
    """
    GET /home/search/filters/?q=...
    Returns available filters (price range, categories) for a search query.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.products.models import Product
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response(
                {"status": "error", "message": "q is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = Product.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )
        return ok("Search filters retrieved.", data=SearchFiltersSerializer(qs).data)




#ANALYTICS & TRACKING
class PageViewTrackView(APIView):
    """
    POST /home/analytics/page-view/
    Body: { "path": "/products/some-slug/", "referrer": "...", "session_key": "..." }
    Fire-and-forget - always returns 200.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = PageViewSerializer(data=request.data, context={"request": request})
        if s.is_valid():
            try:
                s.save()
            except Exception:
                pass
        return ok("Page view recorded.")


class ClickTrackingView(APIView):
    """
    POST /home/analytics/click/
    Body: { "category": "banner", "label": "5", "value": "homepage_hero", "path": "/" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = ClickTrackingSerializer(data=request.data, context={"request": request})
        if s.is_valid():
            try:
                s.save()
            except Exception:
                pass
        return ok("Click recorded.")

class UserActivityLogView(APIView):
    """
    POST /home/analytics/activity/
    Body: { "event_type": "add_to_cart", "category": "product", "label": "42", ... }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = UserActivityLogSerializer(data=request.data, context={"request": request})
        if s.is_valid():
            try:
                s.save()
            except Exception:
                pass
        return ok("Activity recorded.")
    
class AnalyticsEventView(APIView):
    """
    POST /home/analytics/event/
    Generic event recorder. Accepts any event_type + metadata dict.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = AnalyticsEventSerializer(data=request.data, context={"request": request})
        if s.is_valid():
            try:
                s.save()
            except Exception:
                pass
        return ok("Event recorded.")