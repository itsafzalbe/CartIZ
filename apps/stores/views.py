from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone


from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView

from .models import *
from .serializers import *
from apps.utils.response_helpers import *
from apps.utils.permissions import *


# ─────────────────────────────────────────────────────────────────────────────
# Shared market lookup
# ─────────────────────────────────────────────────────────────────────────────

def _get_active_market(pk: int) -> Market | None:
    try:
        return Market.objects.get(pk=pk, is_active=True)
    except Market.DoesNotExist:
        return None

def _get_own_market(user, pk: int) -> Market | None:
    try:
        return Market.objects.get(pk=pk, seller=user)
    except Market.DoesNotExist:
        return None
    

# ═════════════════════════════════════════════════════════════════════════════
# MARKET CRUD
# ═════════════════════════════════════════════════════════════════════════════

class MarketListView(APIView):
    """
    GET /stores/markets/        -> paginated list of all active markets
    POST /stores/markets/       -> create a new market (seller only) 
    """

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get(self, request):
        markets = Market.objects.filter(is_active=True).order_by('-created_at')
        serializer = MarketListSerializer(markets, many=True)
        return ok("Markets retrieved.", data={
            "count": markets.count(),
            "markets": serializer.data
        })
    
    def post(self, request):
        serializer = MarketCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        market = serializer.save()
        return created(
            "Market created successfully. It will be reviewed before going live.",
            data=MarketDetailSerializer(market, context={"request": request}).data
        )


# ─────────────────────────────────────────────────────────────────────────────
class MarketDetailView(APIView):
    """
    GET     /stores/markets/<pk>/       -> full public detail
    PATCH   /stores/markets/<pk>/       -> update (owner only)
    DELETE  /stores/markets/<pk>/       -> soft-delete (owner only)
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get(self, request, pk: int):
        market = _get_active_market(pk)
        if not market:
            return not_found("Market not found.")
        serializer = MarketPublicSerializer(market, context={"request": request})
        return ok("Market retrieved.", data=serializer.data)
    
    def patch(self, request, pk: int):
        market = _get_own_market(request.user, pk)
        if not market:
            return not_found("Market not found or you don't own it.")
        serializer = MarketUpdateSerializer(market, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        market = serializer.save()
        return ok("Market updated.", data=MarketDetailSerializer(market, context={"request": request}).data)
    
    def delete(self, request, pk: int):
        market = _get_own_market(request.user, pk)
        if not market:
            return not_found("Market not found or you don't own it.")
        serializer = MarketDeleteSerializer(data=request.data, context={"request": request, "market": market})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok("Market deactivated successfully.")
    


class MarketFullDetailView(APIView):
    """
    GET /stores/markets/<pk>/detail/
    Full admin/owner detail including private fields
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        # staff can see any; sellers can only see their own
        if request.user.is_staff:
            market = get_object_or_404(Market, pk=pk)
        else:
            market = _get_own_market(request.user, pk)
            if not market:
                return not_found("Market not found or you don't own it.")
        serializer = MarketDetailSerializer(market, context={"request": request})
        return ok("Full market detail retrieved.", data=serializer.data)



class MarketBySlugView(APIView):
    """
    GET /stores/markets/slug/<slug>/
    Public market page via slug (SEO-friendly URL)
    """

    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        market = get_object_or_404(Market, slug=slug, is_active=True)
        serializer = MarketPublicSerializer(market, context={"request": request})
        return ok("Market retrieved.", data=serializer.data)



# ═════════════════════════════════════════════════════════════════════════════
# SELLER'S OWN MARKET
# ═════════════════════════════════════════════════════════════════════════════
class MyMarketView(APIView):
    """
    GET /stores/my-market/
    Returns the authenticated seller's market in management view.
    """

    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = Market.objects.filter(seller=request.user).first()
        if not market:
            return not_found("You don't have a market yet.")
        serializer = MarketSellerSerializer(market, context={"request": request})
        return ok("Your market retrieved.", data=serializer.data)


class MarketStatsView(APIView):
    """
    GET /stores/my-market/stats/
    Performance stats for the seller dashboard.
    """
    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = Market.objects.filter(seller=request.user).first()
        if not market:
            return not_found("You don't have a market yet.")
        serializer = MarketStatsSerializer(market)
        return ok("Stats retrieved.", data=serializer.data)
    

    
class MarketSettingsView(APIView):
    """
    GET     /stores/my-market/settings/     -> view current settings
    PATCH   /stores/my-market/settings/     -> update settings
    """

    permission_classes = [IsSellerOnly]
    def _get_market(self, user):
        return Market.objects.filter(seller=user).first()
    
    def get(self, request):
        market = self._get_market(request.user)
        if not market:
            return not_found("You do not have a market yet")
        serializer = MarketSettingsSerializer(market)
        return ok("Settings retrieved.", data=serializer.data)
    
    def patch(self, request):
        market = self._get_market(request.user)
        if not market:
            return not_found("You do not have a market yet")
        serializer = MarketSettingsSerializer(market, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok("Settings updated.", data=MarketSettingsSerializer(market).data)
        


class MarketVerificationView(APIView):
    """
    POST /stores/my-market/verify/
    Seller submits business info to request verification
    """

    permission_classes = [IsSellerOnly]

    def post(self, request):
        market = Market.objects.filter(seller=request.user).first()
        if not market:
            return not_found("You do not have a market yet.")
        if market.is_verified:
            return Response(
                {"status": "error", "message": "Your market is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = MarketVerificationSerializer(
            data=request.data,
            context={"request": request, "market": market},
            )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok("Verification request submitted. We'll review it shortly.")


class MarketAnalyticsView(APIView):
    """
    GET /stores/my-market/analytics/
    Detailed analytics for the seller dashboard
    """
    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = Market.objects.filter(seller=request.user).first()
        if not market:
            return not_found("You dont have a market yet")
        serializer = MarketAnalyticsSerializer(market)
        return ok("Analytics retrieved.", data=serializer.data)



# ═════════════════════════════════════════════════════════════════════════════
# MARKET DISCOVERY
# ═════════════════════════════════════════════════════════════════════════════

class MarketSearchView(APIView):
    """
    GET /stores/markets/search/?q=<query>/
    Searches by market_name, descriptions, business_address.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response(
                {"status": "error", "message": "Search query is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        markets = Market.objects.filter(is_active=True).filter(
            Q(market_name__icontains=q) |
            Q(description__icontains=q) |
            Q(business_address__icontains=q)
        ).order_by('-rating_average')

        serializer = MarketSearchSerializer(markets, many=True)
        return ok(f"Search results for '{q}'.", data={
            "count": markets.count(),
            "results": serializer.data,
        })
    
class FeaturedMarketsView(APIView):
    """
    GET /stores/markets/featured/
    Verified, active markets stored by total_sales (homepage use).
    """

    permission_classes = [AllowAny]
    
    def get(self, request):
        markets = Market.objects.filter(is_active=True, is_verified=True).order_by('-total_sales')[:12]
        serializer = FeaturedMarketsSerializer(markets, many=True)
        return ok("Featured markets retrieved.", data={"markets": serializer.data})


class PopularMarketsView(APIView):
    """
    GET /stores/markets/popular/
    Top markets by total sales.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        markets = Market.objects.filter(is_active=True).order_by('-total_sales')[:20]
        serializer = PopularMarketsSerializer(markets, many=True)
        return ok("Popular markets retrieved.", data={"markets": serializer.data})
    
    

class MarketBrowseView(APIView):
    """
    GET /stores/markets/browse/
    Paginated browse with optional filters:
        ?verified=true ?min_rating=4 ?sort=rating|sales|newest
    """

    permission_classes = [AllowAny]
    def get(self, request):
        qs = Market.objects.filter(is_active = True)
        
        if request.query_params.get('verified') == 'true':
            qs = qs.filter(is_verified=True)
        
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            try:
                qs = qs.filter(rating_average__gte=float(min_rating))
            except ValueError:
                pass
        
        sort = request.query_params.get('sort', 'newest')
        order_map = {
            'rating': '-rating_average',
            'sales': '-total_sales',
            'newest': '-created_at',
        }
        qs = qs.order_by(order_map.get(sort, '-created_at'))

        serializer = MarketBrowseSerializer(qs, many=True)
        return ok("Markets retrieved.", data={
            "count": qs.count(),
            "markets": serializer.data,
        })


class MarketByCategoryView(APIView):
    """
    GET /stores/markets/by-category/<category_id>/
    Markets that sell products in the given category.
    """    

    permission_classes = [AllowAny]

    def get(self, request, category_id: int):
        markets = Market.objects.filter(
            is_active = True,
            products__category_id = category_id,
            products__is_active = True,
        ).distinct().order_by('-rating_average')

        serializer = MarketCategorySerializer(markets, many = True)
        return ok("Markets in category retrieved.", data={
            "count": markets.count(),
            "markets": [serializer.to_representation(m) for m in markets]
        })


class TrendinMarketsView(APIView):
    """
    GET /stores/markets/trending/
    Markets with the most approved reviews in the last 7 days 
    """

    permission_classes = [AllowAny]

    def get(self, request):
        since = timezone.now() - timezone.timedelta(days=7)
        from django.db.models import Count

        markets = Market.objects.filter(is_active=True).annotate(recent=Count('reviews', filter=Q(reviews__is_approved=True, reviews__created_at__gte=since))).order_by('-recent', '-rating_average')[:20]

        serializer = TrendingMarketsSerializer(markets, many=True)
        return ok("Trending markets retrieved.", data={"markets": serializer.data})
    
# ═════════════════════════════════════════════════════════════════════════════
# MARKET REVIEWS
# ═════════════════════════════════════════════════════════════════════════════
class MarketReviewListCreateView(APIView):
    """
    GET /stores/markets/<pk>/reviews/           -> list approved reviews
    POST /stores/markets/<pk>/reviews/          -> create reveiw (auth required)
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, pk: int):
        market = _get_active_market(pk)
        if not market:
            return not_found("Market not found.")
        reviews = market.reveiws.filter(is_approved=True).order_by('-created_at')
        serializer = MarketReviewSerializer(reviews, many=True)
        return ok("Reviews retrieved.", data={
            "count": reviews.count(),
            "reviews": serializer.data,
        })
    
    def post(self, request, pk: int):
        market = _get_active_market(pk)
        if not market:
            return not_found("Market not found.")

        serializer = MarketReviewCreateSerializer(
            data=request.data,
            context={"request": request, "market": market},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return created(
            "Review submitted. It will appear after approval.",
            data = MarketReviewSerializer(review).data,
        )
    
class MarketReviewDetailView(APIView):
    """
    GET     /stores/markets/reviews/<pk>/   -> fill review detail
    PATCH   /stores/markets/reviews/<pk>/   -> edit own review
    DELETE  /stores/markets/reviews/<pk>/   -> delete own review
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_review(self, pk):
        try:
            return MarketReview.objects.select_related('user', 'market', 'order').get(pk=pk)
        except MarketReview.DoesNotExist:
            return None

    def get(self, request, pk: int):
        review = self._get_review(pk)
        if not review:
            return not_found("Review not found.")
        serializer = MarketReviewDetailSerializer(review, context={"request": request})
        return ok("Review retrieved.", data=serializer.data)
    
    def patch(self, request, pk: int):
        review = self._get_review(pk)

        if not review:
            return not_found("Review not found.")
        if review.user_id != request.user.pk:
            return forbidden("You can only edit your own reviews.")
        
        serializer = MarketReviewUpdateSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return ok("Review updated.", data=MarketReviewDetailSerializer(review, context={"request": request}).data)

    def delete(self, request, pk: int):
        review = self._get_review(pk)
        if not review:
            return not_found("Review not found.")
        serializer = MarketReviewDeleteSerializer(
            data={},
            context={"request": request, "review": review},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok("Review deleted.")


class MarketReviewStatsView(APIView):
    """
    GET /stores/markets/<pk>/reviews/stats/
    Rating breakdown for a market's review section.
    """

    permission_classes = [AllowAny]

    def get(self, request, pk: int):
        market = _get_active_market(pk)
        if not market:
            return not_found("Market not found.")
        serializer = MarketReviewStatsSerializer(market)
        return ok("Review stats retrieved.", data=serializer.data)
        













# # ═════════════════════════════════════════════════════════════════════════════
# # MARKET FOLLOWERS
# # Note: placeholder views — swap body for real logic once MarketFollower
# # model is added.
# # ═════════════════════════════════════════════════════════════════════════════

# class MarketFollowView(APIView):
#     """
#     POST   /stores/markets/<pk>/follow/     → follow
#     DELETE /stores/markets/<pk>/follow/     → unfollow
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk: int):
#         market = _get_active_market(pk)
#         if not market:
#             return not_found("Market not found.")

#         serializer = FollowMarketSerializer(
#             data={},
#             context={"request": request, "market": market},
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return ok(f"You are now following {market.market_name}.")

#     def delete(self, request, pk: int):
#         market = _get_active_market(pk)
#         if not market:
#             return not_found("Market not found.")

#         serializer = UnfollowMarketSerializer(
#             data={},
#             context={"request": request, "market": market},
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return ok(f"You have unfollowed {market.market_name}.")


# class MarketFollowersListView(APIView):
#     """
#     GET /stores/markets/<pk>/followers/
#     Lists all followers of a market (owner / staff only).
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk: int):
#         market = get_object_or_404(Market, pk=pk)
#         if market.seller_id != request.user.pk and not request.user.is_staff:
#             return forbidden("Only the market owner can view followers.")
#         serializer = MarketFollowersListSerializer(market)
#         return ok("Followers retrieved.", data=serializer.data)


# class FollowedMarketsView(APIView):
#     """
#     GET /stores/markets/following/
#     Markets the authenticated user is following.
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         # Replace with real queryset once MarketFollower model is added:
#         # markets = Market.objects.filter(followers__user=request.user, is_active=True)
#         markets    = Market.objects.none()
#         serializer = FollowedMarketsSerializer(markets, many=True)
#         return ok("Followed markets retrieved.", data={
#             "count":   0,
#             "markets": serializer.data,
#         })