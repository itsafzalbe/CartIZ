
from rest_framework.permissions import IsAuthenticated


# ─────────────────────────────────────────────────────────────────────────────
# Custom permissions
# ─────────────────────────────────────────────────────────────────────────────

class IsSellerOnly(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_seller

class IsMarketOwner(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_seller
    

