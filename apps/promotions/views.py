from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Coupon, CouponUsage, FlashSale, Promotion
from .serializers import (
    ActiveDealsSerializer,
    BundleDealsSerializer,
    ClearanceSaleSerializer,
    CouponActiveSerializer,
    CouponApplySerializer,
    CouponCreateSerializer,
    CouponDeleteSerializer,
    CouponDetailSerializer,
    CouponListSerializer,
    CouponPublicSerializer,
    CouponSerializer,
    CouponStatsSerializer,
    CouponUpdateSerializer,
    CouponUsageListSerializer,
    CouponUsageSerializer,
    CouponUsageStatsSerializer,
    CouponValidateSerializer,
    DealOfTheDaySerializer,
    ExpiredDealsSerializer,
    FlashSaleCreateSerializer,
    FlashSaleSerializer,
    FlashSaleUpdateSerializer,
    PromotionCreateSerializer,
    PromotionDetailSerializer,
    PromotionListSerializer,
    PromotionSerializer,
    PromotionStatsSerializer,
    PromotionUpdateSerializer,
    SeasonalSaleSerializer,
    UpcomingDealsSerializer,
)

from apps.utils.response_helpers import *
from apps.utils.permissions import *

CART_COUPON_KEY = 'cart_coupon'


#Shared ownership helpers
def _owns_coupon(user, coupon: Coupon) -> bool:
    return user.is_staff or coupon.market.seller_id == user.pk

def _owns_flash_sale(user, sale: FlashSale) -> bool:
    return user.is_staff or sale.market.seller_id == user.pk

def _owns_promotion(user, promo: Promotion) -> bool:
    return user.is_staff or (promo.market and promo.market.seller_id == user.pk)


#COUPONS
class CouponListCreateView(APIView):
    """
    GET     /promotions/coupons/    -> seller sees own; admin sees all
    POST    /promotions/coupons/    -> create (seller)
    """

    def get_permissions(self):
        return [IsSellerOnly()] if self.request.method == 'POST' else [IsAuthenticated()]

    def get(self, request):
        user = request.user
        if user.is_staff:
            qs = Coupon.objects.all()
        else:
            qs = Coupon.objects.filter(market__seller=user)
        
        #optional filters
        if request.query_params.get('active') == 'true':
            now = timezone.now()
            qs = qs.filter(is_active=True, valid_from__lte=now, valid_until__gte=now)
        
        qs = qs.order_by('-created_at')
        return ok("Coupons retrieved.", data={"count": qs.count(), "coupons": CouponListSerializer(qs, many=True).data})
    
    def post(self, request):
        s = CouponCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        coupon = s.save()
        return created("Coupon created.", data=CouponSerializer(coupon).data)


class CouponDetailView(APIView):
    """
    GET     /promotions/coupons/<id>/ 
    PATCH   /promotions/coupons/<id>/   -> update (owner)
    DELETE  /promotions/coupons/<id>/   -> deactivate (owner)
    """
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        return get_object_or_404(Coupon, pk=pk)

    def get(self, request, pk):
        coupon = self._get(pk)
        if not _owns_coupon(request.user, coupon):
            return forbidden()
        return ok("Coupon retrieved.", data=CouponDetailSerializer(coupon).data)
    
    def patch(self, request, pk):
        coupon = self._get(pk)
        if not _owns_coupon(request.user, coupon):
            return forbidden()
        s = CouponUpdateSerializer(coupon, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Coupon updated.", data=CouponSerializer(s.save()).data)
    
    def delete(self, request, pk):
        coupon = self._get(pk)
        if not _owns_coupon(request.user, coupon):
            return forbidden()
        CouponDeleteSerializer(data={}, context={"coupon": coupon}).save()
        return ok("Coupon deactivated.")


class CouponStatsView(APIView):
    """
    GET /promotions/coupons/<id>/stats/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        coupon = get_object_or_404(Coupon, pk)
        if not _owns_coupon(request.user, coupon):
            return forbidden()
        return ok("Coupon retrieved.", data=CouponStatsSerializer(coupon).data)


class CouponPublicListView(APIView):
    """
    GET /promotions/coupons/public/?market_id=<id>
    Publicly available coupons for a market's storefront.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        market_id = request.query_params.get('market_id')
        now = timezone.now()
        qs = Coupon.objects.filter(
            is_active=True, valid_from__lte=now, valid_until__gte=now,
        )
        if market_id:
            qs = qs.filter(market_id=market_id)
        return ok("Public coupons retrieved.", data={"coupons": CouponPublicSerializer(qs, many=True).data})

class CouponsActiveListView(APIView):
    """
    GET /promotions/coupons/active/?market_id=<id>
    Currently active coupons - used in cart paget dropdown.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        market_id = request.query_params.get('market_id')
        qs = Coupon.objects.filter(
            is_active=True, valid_from__lte=now, valid_until__gte=now,
        )
        if market_id:
            qs = qs.filter(market_id=market_id)
        return ok("Active coupons retrieved.", data={"coupons": CouponActiveSerializer(qs, many=True).data})


class CouponValidateView(APIView):
    """
    POST /promotions/coupons/validate/
    Body: { "code": "SAVE20", "cart_total": "99.99" }
    Validates a coupon without applying it.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CouponValidateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        return ok("Coupon is valid.", data=s.get_discount())


class CouponApplyView(APIView):
    """
    POST /promotions/coupons/apply/
    Body: { "code": "SAVE20" }
    Applies coupon to cart session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CouponApplySerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)

        try:
            from apps.cart.models import Cart
            cart = Cart.objects.get(user=request.user)
            cart_total = sum(item.total_price for item in cart.items.all())
        except Exception:
            cart_total = Decimal('0.00')
        
        discount = s.compute_discount(cart_total)
        coupon = s.get_coupon()

        request.session[CART_COUPON_KEY] = {
            "code":     coupon.code,
            "discount": str(discount),
        }
        
        return ok("Coupon applied.", data={
            "coupon_code":      coupon.code,
            "discount_amount":  str(discount),
            "discount_type":    coupon.discount_type,

        })


#COUPON USAGE
class CouponUsageLisView(APIView):
    """
    GEt /promotions/coupons/<id>/usage/
    Seller views usage history for a specific coupon.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        if not _owns_coupon(request.user, coupon):
            return forbidden()
        usages = coupon.usages.order_by('-used_at')
        return ok("Usage history retrieved.", data={
            "count":    usages.count(),
            "usages": CouponUsageListSerializer(usages, many=True).data,
        })


class CouponUsageStatsView(APIView):
    """
    GET /promotions/coupons/usage/stats/
    Aggregated usage stats for the seller's all coupons.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            qs = CouponUsage.objects.all()
        else:
            qs = CouponUsage.objects.filter(coupon__market__seller=user)
        return ok("Usage stats retrieved.", data=CouponUsageStatsSerializer(qs).data)


class MyCouponUsageView(APIView):
    """
    GET /promotions/my-usage/
    Buyer views their own coupon usage history.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usages = CouponUsage.objects.filter(user=request.user).order_by('-used_at')
        return ok("Your coupon usage retrieved.", data={
            "count": usages.count(),
            "usages": CouponUsageSerializer(usages, many=True).data,
        })




#FLASH SALES
class FlashSaleListCreateView(APIView):
    """
    GET     /promotions/flash-sales/    -> active flash sales (public)
    POST    /promotions/flash-sales/    -> create (seller)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        return [IsSellerOnly()] if self.request.method == 'POST' else [AllowAny()]
    
    def get(self, request):
        now = timezone.now()
        qs = FlashSale.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now)

        market_id = request.query_params.get('market_id')
        if market_id:
            qs = qs.filter(market_id=market_id)

        return ok("Flash sales retrieved.", data={
            "count":    qs.count(),
            "sales":    FlashSaleSerializer(qs, many=True).data,
        })
    
    def post(self, request):
        s = FlashSaleCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        sale = s.save()
        return created("Flash sale created.", data=FlashSaleSerializer(sale).data)


class FlashSaleDetailView(APIView):
    """
    GET     /promotions/flash-sales/<pk>/ 
    PATCH   /promotions/flash-sales/<pk>/   -> update (owner)
    DELETE  /promotions/flash-sales/<pk>/   -> deactivate (owner)
    """

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]
    
    def _get(self, pk):
        return get_object_or_404(FlashSale, pk=pk)
    
    def get(self, request, pk):
        return ok("Flash sale retrieved.", data=FlashSaleSerializer(self._get(pk)).data)
    
    def patch(self, request, pk):
        sale = self._get(pk)
        if not _owns_flash_sale(request.user, sale):
            return forbidden()
        s = FlashSaleUpdateSerializer(sale, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Flash sale updated.", data=FlashSaleSerializer(s.save()).data)
    
    def delete(self, request, pk):
        sale = self._get(pk)
        if not _owns_flash_sale(request.user, sale):
            return forbidden()
        sale.is_active = False
        sale.save(update_fields=['is_active'])
        return ok("Flash sale deactivated.")


class DealOfTheDayView(APIView):
    """
    GET /promotions/deal-of-the-day/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        deal = FlashSale.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now).order_by('-discount_percent').first()
        if not deal:
            return not_found("No deal of the day available.")
        return ok("Deal of the day retrieved.", data=DealOfTheDaySerializer(deal).d)


class ActiveDealsView(APIView):
    """GET /promotions/active/ - all currently live products."""
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now)
        return ok("Active deals retrieved.", data={
            "count": qs.count(),
            "deals": ActiveDealsSerializer(qs, many=True).data
        })




class UpcomingDealsView(APIView):
    """GET /promotions/upcoming/"""
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(is_active=True, starts_at__gt=now).order_by('starts_at')
        return ok("Upcoming deals retrieved.", data={
            "count":    qs.count(),
            "deals":    UpcomingDealsSerializer(qs, many=True).data,
        })


class ExpiredDealsView(APIView):
    """GET /promotions/expired/ - seller's own expired deals."""
    permission_classes = [IsSellerOnly]

    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(market__seller=request.user, ends_at__lt=now).order_by('-ends_at')
        return ok("Expired deals retrieved.", data={
            "count": qs.count(),
            "deals": ExpiredDealsSerializer(qs, many=True).data
        })

class ClearanceSaleView(APIView):
    """GET /promotions/clearance/"""
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(
            is_active=True,
            promo_type=Promotion.CLEARANCE,
            starts_at__lte=now,
            ends_at__gte=now,
        )

        return ok("Clearance sales retrieved.", data={"sales": ClearanceSaleSerializer(qs, many=True).data})


class SeasonalSaleView(APIView):
    """GET /promotions/seasonal/"""
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(
            is_active=True,
            promo_type=Promotion.SEASONAL,
            starts_at__lte=now,
            ends_at__gte=now,
        )

        return ok("Seasonal sales retrieved.", data={"sales": SeasonalSaleSerializer(qs, many=True).data})

class BundleDealsView(APIView):
    """GET /promotions/bundles/"""
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(
            is_active=True,
            promo_type=Promotion.BUNDLE,
            starts_at__lte=now,
            ends_at__gte=now,
        )

        return ok("Bundle deals retrieved.", data={"deals": BundleDealsSerializer(qs, many=True).data})
    

#PROMOTIONS
class PromotionListCreateView(APIView):
    """
    GET /promotions     -> list active promotions (public)
    POST /promotions    -> create promotion (seller, admin)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == 'POST' else [AllowAny()]
    
    def get(self, request):
        now = timezone.now()
        qs = Promotion.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now)

        promo_type = request.query_params.get('type')
        if promo_type:
            qs = qs.filter(promo_type=promo_type)
        
        market_id = request.query_params.get('market_id')
        if market_id:
            qs = qs.filter(market_id=market_id)
        
        featured = request.query_params.get('featured')
        if featured == 'true':
            qs = qs.filter(is_featured=True)
        
        qs = qs.order_by('-is_featured', '-created_at')
        return ok("Promotions retrieved.", data={
            "count":    qs.count(),
            "promotions":   PromotionListSerializer(qs, many=True).data
        })
    
    def post(self, request):
        s = PromotionCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        promo = s.save()
        return created("Promotion created.", data=PromotionDetailSerializer(promo).data)

class PromotionDetailView(APIView):
    """
    GET     /promotions/<pk>/
    PATCH   /promotions/<pk>/       -> update (owner)
    DELETE  /promotions/<pk>/       -> deactivate (owner)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]
    
    def _get(self, pk):
        return get_object_or_404(Promotion, pk=pk)
    
    def get(self, request, pk):
        promo = self._get(pk)
        #here we increment the view count 
        Promotion.objects.filter(pk=pk).update(view_count=promo.view_count + 1)
        return ok("Promotion retrieved.", data=PromotionDetailSerializer(promo).data)
    
    def patch(self, request, pk):
        promo = self._get(pk)
        if not _owns_coupon(request.user, promo):
            return forbidden()
        s = PromotionUpdateSerializer(promo, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Promotion updated.", data=PromotionDetailSerializer(s.save()).data)
    
    def delete(self, request, pk):
        promo = self._get(pk)
        if not _owns_coupon(request.user, promo):
            return forbidden()
        promo.is_active = False
        promo.save(update_fields=['is_active'])
        return ok("Promotion deactivated.")

class PromotionStatsView(APIView):
    """GET /promotions/<pk>/stats/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        if not _owns_promotion(request.user, promo):
            return forbidden()
        return ok("Promotion stats retrieved.", data=PromotionStatsSerializer(promo).data)


class PromotionClickView(APIView):
    """
    POST /promotions/<pk>/click/
    Tracks a click on a promotion banner.
    """
    permission_classes = [AllowAny]

    def post(self, request, pk):
        Promotion.objects.filter(pk=pk).update(click_count=Promotion.objects.get(pk=pk).click_count + 1)
        return ok("Click recorded.")

class SellerPromotionListView(APIView):
    """GET /promotions/my-promotions/ - seller's own promotions."""
    permission_classes = [IsSellerOnly]

    def get(self, request):
        qs = Promotion.objects.filter(market__seller=request.user).order_by('-created_at')
        return ok("Your promotions retrieved.", data={
            "count": qs.count(),
            "promotions": PromotionListSerializer(qs, many=True).data
        })