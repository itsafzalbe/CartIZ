"""
Seller views — backed by the Market model.
Replace the 5 SellerProfile-based views in accounts/views.py with these.

Also update the seller view imports at the top of accounts/views.py:
  from .seller_serializers import (
      BecomeSellerSerializer,
      SellerProfileSerializer,
      SellerProfileUpdateSerializer,
      SellerPublicSerializer,
      SellerStatsSerializer,
  )
"""

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stores.models import *
from .seller_serializers import *




# ═════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═════════════════════════════════════════════════════════════════════════════

def success(message: str, data: dict = None, http_status=status.HTTP_200_OK) -> Response:
    body = {"status": "success", "message": message}
    if data is not None:
        body["data"] = data
    return Response(body, status=http_status)


def created(message: str, data: dict = None) -> Response:
    return success(message, data, http_status=status.HTTP_201_CREATED)

class IsSellerOnly(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_seller

def _get_market(user) -> Market | None:
    """Returns the seller's primary market or None."""
    return Market.objects.filter(seller=user).first()

# ─────────────────────────────────────────────────────────────────────────────

class BecomeSellerView(APIView):
    """
    POST /accounts/me/become-seller/
    Creates the user's first Market and sets is_seller = True
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BecomeSellerSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return created(
            "Seller account created. Your market is under review.",
            data={"market_id": self.market.pk, "slug": self.market.slug, "is_active": self.market.is_active})


class SellerProfileView(APIView):
    """
    GET /accounts/me/seller/
    Returns the authenticated seller's full market profile.
    """

    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = _get_market(request.user)
        if not market:
            return Response(
                {
                    "status": "error", 
                    "message": "Market not Found."
                }, status=status.HTTP_404_NOT_FOUND,
            )
        return success("Market profile retrieved.", data=SellerProfileSerializer(market).data)


class SellerProfileUpdateView(APIView):
    """
    PATCH /accounts/me/seller/update/
    Update mutable market fields. Accepts multipart for image uploads
    """

    permission_classes = [IsSellerOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request):
        market = _get_market(request.user)
        if not market:
            return Response(
                {
                "status": "error",
                "message": "Market not found",
                }, status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = SellerProfileUpdateSerializer(market, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success("Market updated.", data=SellerProfileSerializer(market).data)
    



class SellerPublciView(APIView):
    """
    GET /accounts/sellers/<seller_id>
    Public market card - no authentication required 
    Uses Market PK; you can also add a slug based variant
    """
    permission_classes = [AllowAny]

    def get(self, request, seller_id: int):
        from django.shortcuts import get_object_or_404
        market = get_object_or_404(Market, pk=seller_id, is_active=True)
        return success("Market retrieved.", data=SellerPublicSerializer(market).data)



class SellerStatsView(APIView):
    """
    GET /accounts/me/seller/stats/
    Performance metrics for the seller dashboard.
    """
    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = _get_market(request.user)
        if not market:
            return Response(
                {"status": "error", "message": "Market not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SellerStatsSerializer(market)
        return success("Stats retrieved.", data=serializer.data)





