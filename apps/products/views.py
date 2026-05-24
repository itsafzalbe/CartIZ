"""
products/views.py
=================
Permissions:
    AllowAny            - public product/category browsing
    IsAuthenticated     - reviews, wishlists
    IsSellerOnly        - create/update/delete own products
    IsAdminUser         - category/attribute management
"""

from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .serializers import *
from apps.utils.response_helpers import *
from apps.utils.permissions import *


# ─────────────────────────────────────────────────────────────────────────────
# Filtering helper
# ─────────────────────────────────────────────────────────────────────────────

def _apply_filters(qs, params):
    """Apply ProductFilterSerializer validated params to a queryset."""

    if params.get('q'):
        qs = qs.filter(
            Q(name__icontains=params['q']) |
            Q(description__icontains=params['q']) |
            Q(sku__icontains=params['q'])
        )
    if params.get('category'):
        qs = qs.filter(category_id=params['category'])
    if params.get('min_price') is not None:
        qs = qs.filter(price__gte=params['min_price'])
    
    if params.get('max_price') is not None:
        qs = qs.filter(price__lte=params['max_price'])

    if params.get('min_rating') is not None:
        qs = qs.filter(rating_average__gte=params['min_rating'])
    if params.get('in_stock') is True:
        qs = qs.filter(stock_quantity__gt=0)
    if params.get('is_featured') is not None:
        qs = qs.filter(is_featured=params['is_featured'])
    if params.get('market'):
        qs = qs.filter(market_id=params['market'])
    
    sort_map = {
        'price_asc':    'price',
        'price_desc':   '-price',
        'rating':       '-rating_average',
        'newest':       '-created_at',
        'popular':      '-view_count',
        'sales':        '-sold_count',
    }
    sort = params.get('sort', 'newest')
    qs = qs.order_by(sort_map.get(sort, '-created_at'))
    return qs


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ═════════════════════════════════════════════════════════════════════════════
class CategoryListCreateView(APIView):
    """
    GET /products/categories/   -> list active categories
    POST /products/categories/  -> create category (admin)
    """

    def get_permissions(self):
        return [IsAdminUser()] if self.request.method == "POST" else [AllowAny()]

    def get(self, request):
        categories = Category.objects.filter(is_active=True, parent_id__isnull=True).order_by('order_position')
        return ok("Categories retrieved.", data={"categories": CategoryListSerializer(categories, many=True).data})

    def post(self, request):
        s = CategoryCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        cat = s.save()
        return created("Category created.", data=CategorySerializer(cat).data)

class CategoryDetailView(APIView):
    """
    GET     /products/categories/<id>/      -> detail with subcategories
    PATCH   /products/categories/<id>/      -> update (admin)
    DELETE  /products/categories/<id>/      -> soft-delete (admin)
    """

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAdminUser()]
    
    def _get(self, pk):
        return get_object_or_404(Category, pk=pk, is_active=True)

    def get(self, pk):
        return ok("Category retrieved.", data=CategoryDetailSerializer(self._get(pk)).data)
    
    def patch(self, request, pk):
        cat = self._get(pk)
        s = CategoryUpdateSerializer(cat, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Category updated.", data=CategorySerializer(s.save()).data)
    
    def delete(self, request, pk):
        cat = self._get(pk)
        CategoryDeleteSerializer(data={}, context={'category': cat}).save()
        return ok("Category deactivated.")

class CategoryTreeView(APIView):
    """GET /products/categories/tree/   -full nested tree"""
    permission_classes = [AllowAny]

    def get(self, request):
        roots = Category.objects.filter(is_active=True, parent_id__isnull=True).order_by('order_position')
        return ok("Category tree retrieved.", data={"tree": CategoryTreeSerializer(roots, many=True).data})

class CategoryBrowseView(APIView):
    """GET /products/categories/<id>/browse/ - category page with subcategories."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk, is_active=True)
        return ok("Category browse data retrieved.", data=CategoryBrowseSerializer(cat).data)



class PopularCategoriesView(APIView):
    """GET /products/categories/popular/"""

    permission_classes = [AllowAny]

    def get(self, request):
        cats = Category.objects.filter(is_active=True).annotate(
            count=Count('products', filter=Q(products__is_active=True))
        ).order_by('-count')[:12]
        return ok("Popular categories retrieved.", data={"categories": PopularCategoriesSerializer(cats, many=True).data})


class CategoryWithTopProductsView(APIView):
    """GET /products/categories/with-products/ - each category + top 4 products."""
    permission_classes = [AllowAny]

    def get(self, request):
        cats = Category.objects.filter(is_active=True, parent_id__isnull=True).order_by('order_position')[:8]
        return ok("Categories with products retrieved.", data={"categories": CategoryWithTopProductsSerializer(cats, many=True).data})


class CategoryBreadcrumbView(APIView):
    """GET /products/categories/<id>/breadcrumb/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        return ok("Breadcrumb retrieved.", data=CategoryBreadcrumbSerializer(cat).data)


class SubcategoryListView(APIView):
    """GET /products/categories/<id>/subcategories/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk, is_active=True)
        subs = cat.Children.filter(is_active=True).order_by('order_position')
        return ok("Subcategories retrieved.", data={"subcategories": SubcategoryListSerializer(subs, many=True).data})


class CategoryProductListSerializer(APIView):
    """GET /products/categories/<id>/products/ - products in a category with filters"""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk, is_active=True)
        qs = Product.objects.filter(category=cat, is_active=True)

        filter_s = ProductFilterSerializer(data=request.query_params)
        if filter_s.is_valid():
            qs = _apply_filters(qs, filter_s.validated_data)

        return ok("Product retrieved.", data={
            "category":     CategorySerializer(cat).data,
            "count":        qs.count(),
            "products":     CategoryProductListSerializer(qs, many=True).data,
        })

class ProductListCreateView(APIView):
    """
    GET /products/          ->lists all active products (with filters)
    POST /products/         ->create products (seller)
    """

    def get_permissions(self):
        return [IsSellerOnly()] if self.request.method == 'POST' else [AllowAny()]

    
    def get(self, request):
        qs = Product.objects.filter(is_active=True).select_related('market', 'category')
        filter_s = ProductFilterSerializer(data=request.query_params)
        if filter_s.is_valid():
            qs = _apply_filters(qs, filter_s.validated_data)
        return ok("Products retrieved.", data={"count": qs.count(), "products": ProductListSerializer(qs, many=True).data})
    
    def post(self, request):
        s = ProductCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        product = s.save()
        return created("Product created.", data=ProductDetailSerializer(product).data)



class ProductDetailView(APIView):
    """
    GET     /products/<slug>/       -> public product detail (increments the view count)
    PATCH   /products/<slug>/       -> update (owner seller)
    DELETE  /products/<slug>/       -> soft-delete (owner seller)
    """

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsSellerOnly()]

    def _get(self, slug):
        return get_object_or_404(Product, slug=slug, is_active=True)

    
    def get(self, request, slug):
        product = self._get(slug)
        Product.objects.filter(pk=product.pk).update(view_count=product.view_count + 1)
        return ok("Product retrieved.", data=ProductDetailSerializer(product).data)
    
    def patch(self, request, slug):
        product = self._get(slug)
        if product.market.seller_id != request.user.pk:
            return forbidden("You do not own this product.")
            s = ProductUpdateSerializer(product, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            return ok("Product updated.", data=ProductDetailSerializer(s.save()).data)
        
    def delete(self, request, slug):
        product = self._get(slug)
        if product.market.seller_id != request.user.pk:
            return forbidden("You don't own this market.")
        ProductDeleteSerializer(data={}, context={"product": product}).save()
        return ok("Product deactivated.")

class ProductQuickView(APIView):
    """
    GET /products/<slug>/quick-view/
    """

    permission_classes = [AllowAny]
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        return ok("Quick view data retrieved.", data=ProductQuickViewSerializer(product).data)


class ProductStatsView(APIView):
    """GET /products/<slug>/stats/ - seller only."""
    permission_classes = [IsSellerOnly]

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        if product.market.seller_id != request.user.pk:
            return forbidden()
        return ok("Stats retrieved.", data=ProductStatsSerializer(product).data)


# ─────────────────────────────────────────────────────────────────────────────
# Seller's own products
# ─────────────────────────────────────────────────────────────────────────────

class SellerProductListView(APIView):
    """
    GET /products/my-products/ - seller's management view.
    """
    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = request.user.markets.filter(is_active=True).first()
        if not market:
            return not_found("You don't have an active market.")
        qs = market.products.all().order_by('-created_at')
        return ok("Your products retrieved.", data={"count": qs.count(), "products": ProductSellerSerializer(qs, many=True).data})
    


class ProductStockView(APIView):
    """
    GET /products/<slug>/stock/
    PATCH /products/<slug>/stock/   -> updates stock (seller)
    """
    permission_classes = [IsSellerOnly]

    def _get(self, slug, user):
        product = get_object_or_404(Product, slug=slug)
        if product.market.seller_id != user.pk:
            return None, forbidden()
        return product, None
    
    def get(self, request, slug):
        product, err = self._get(slug, request.user)
        if err:
            return err
        return ok("Stock info retrieved.", data=ProductStockSerializer(product).data)
    
    def patch(self, request, slug):
        product, err = self._get(slug, request.user)
        if err:
            return err
        s = ProductStockUpdateSerializer(product, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Stock updated.", data=ProductStockSerializer(s.save()).data)


class LowStockProductsView(APIView):
    """GET /products/my-products/low-stock/         -> seller only"""
    permission_classes = [IsSellerOnly]

    def get(self, request):
        market = request.user.markets.filter(is_active=True).first()
        if not market:
            return not_found("You do not have an active market.")
        qs = market.products.filter(is_active=True).extra(
            where=["stock_quantity <= low_stock_threshold"]
        )
        return ok("Low stock products retrieved.", data={"count": qs.count(), "products": ProductLowStockSerializer(qs, many=True).data})

# ═════════════════════════════════════════════════════════════════════════════
# IMAGES
# ═════════════════════════════════════════════════════════════════════════════

class ProductImageListCreateView(APIView):
    """
    GET /products/<slug>/images/
    POST /products/<slug>/images/   -> uploaf image (seller)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        return [IsSellerOnly()] if self.request.method == 'POST' else [AllowAny()]
    
    def _get_product(self, slug):
        return get_object_or_404(Product, slug=slug, is_active=True)
    
    def get(self, request, slug):
        product = self._get_product(slug)
        images = product.product_images.order_by('order_position')
        return ok("Images retrieved.", data={"images": ProductImageListSerializer(images, many=True).data})
    
    def post(self, request, slug):
        product = self._get_product(slug)
        if product.market.seller_id != request.user.pk:
            return forbidden()
        s = ProductImageCreateSerializer(data=request.data, context={"product": product})
        s.is_valid(raise_exception=True)
        image = s.save()
        return created("Image uploaded.", data=ProductImageSerializer(image).data)


class ProductImageDetailView(APIView):
    """
    PATCH /products/images/<pk>/
    DELETE /products/images/<pk>/
    """

    permission_classes = [IsSellerOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get(self, pk, user):
        img = get_object_or_404(ProductImage, pk=pk)
        if img.product.market.seller_id != user.pk:
            return None, forbidden()
        return img, None
    
    def patch(self, request, pk):
        img, err = self._get(pk, request.user)
        if err:
            return err
        s = ProductImageUpdateSerializer(img, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Image updated.", data=ProductImageSerializer(s.save()).data)
    
    def delete(self, request, pk):
        img, err = self._get(pk, request.user)
        if err:
            return err
        s = ProductImageDeleteSerializer(data={}, context={"image": img})
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Image deleted.")


class SetPrimaryImageView(APIView):
    """PATCH /products/images/<pk>/set-primary/"""

    def patch(self, request, pk):
        img = get_object_or_404(ProductImage, pk=pk)
        if img.product.market.seller_id != request.user.pk:
            return forbidden()
        SetPrimaryImageSerializer(data={}, context={"image": img}).save()
        return ok("Primary image updated.")

class ProductImageBulkUploadView(APIView):
    """POST /products/<slug>/images/bulk/"""
    permission_classes = [IsSellerOnly]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        if product.market.seller_id != request.user.pk:
            return forbidden()
        s = ProductImageBulkUploadSerializer(data=request.data, context={"product": product})
        s.is_valid(raise_exception=True)
        images = s.save()
        return created(f"{len(images)} image(s) uploaded.", data=ProductImageListSerializer(images, many=True).data)



# ═════════════════════════════════════════════════════════════════════════════
# VARIANTS
# ═════════════════════════════════════════════════════════════════════════════

class ProductVariantListCreateView(APIView):
    """
    GET /products/<slug>/variants/
    POST /products/<slug>/variants/     -> create variant seller only
    """

    def get_permissions(self):
        return [IsSellerOnly()] if self.request.method == 'POST' else [AllowAny()]
    
    def _get_product(self, slug):
        return get_object_or_404(Product, slug=slug, is_active=True)
    
    def get(self, request, slug):
        product = self._get_product(slug)
        variants = product.product_variants.filter(is_active=True)
        return ok("Variants retrieved.", data={"variants": ProductVariantListSerializer(variants, many=True).data})
    
    def post(self, request, slug):
        product = self._get_product(slug)
        if product.market.seller_id != request.user.pk:
            return forbidden()
        s = ProductVariantCreateSerializer(data=request.data, context={"product": product})
        s.is_valid(raise_exception=True)
        variant = s.save()
        return created("Variant created.", data=ProductVariantSerializer(variant).data)
        

class ProductVariantDetailView(APIView):
    """
    GET     /products/variatns/<pk>/
    PATCH   /products/variatns/<pk>/
    DELETE  /products/variatns/<pk>/
    """

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsSellerOnly()]
    
    def _get(self, pk):
        return get_object_or_404(ProductVariant, pk=pk)
    
    def get(self, request, pk):
        return ok("Variant retrieved.", data=ProductVariantSerializer(self._get(pk)).data)
    
    def patch(self, request, pk):
        variant = self._get(pk)
        if variant.product.market.seller_id != request.user.pk:
            return forbidden()
        s = ProductVariantUpdateSerializer(variant, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Variant updated.", data=ProductVariantSerializer(s.save()).data)
    
    def delete(self, request, pk):
        variant = self._get(pk)
        if variant.product.market.seller_id != request.user.pk:
            return forbidden()
        ProductVariantDeleteSerializer(data={}, context={"variant": variant}).save()
        return ok("Variant deactivated.")


class ProductVariantStockView(APIView):
    """GET /products/variants/<pk>/stock/"""
    permission_classes = [IsSellerOnly]

    def get(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        if variant.product.market.seller_id != request.user.pk:
            return forbidden()
        return ok("Variant stock retrieved.", data=ProductVariantStockSerializer(variant).data)


# ═════════════════════════════════════════════════════════════════════════════
# ATTRIBUTES
# ═════════════════════════════════════════════════════════════════════════════

class AttributeListCreateView(APIView):
    """
    GET /products/attributes/
    POST /products/attributes/  -> admin only
    """

    def get_permissions(self):
        return [IsAdminUser()] if self.request.method == 'POST' else [AllowAny()]
    
    def get(self, request):
        attrs = ProductAttribute.objects.all().order_by('name')
        return ok("Attributes retrieved.", data={"attributes": ProductAttributeListSerializer(attrs, many=True).data})
    
    def post(self, request):
        s = ProductAttributeCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        attr = s.save()
        return created("Attribute created.", data=ProductAttributeSerializer(attr).data)


class AttributeDetailView(APIView):
    """
    GET     /products/attributes/<pk>/
    PATCH   /products/attributes/<pk>/  -> admin only
    DELETE  /products/attributes/<pk>/  -> admin only
    """

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdminUser()]
    
    def _get(self, pk):
        return get_object_or_404(ProductAttribute, pk=pk)
    
    def get(self, request, pk):
        return ok("Attribute retrieved.", data=ProductAttributeSerializer(self._get(pk)).data)
    
    def patch(self, request, pk):
        attr = self._get(pk)
        s = ProductAttributeUpdateSerializer(attr, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Attribute updated.", data=ProductAttributeSerializer(s.save()).data)
    
    def delete(self, request, pk):
        attr = self._get(pk)
        ProductAttributeDeleteSerializer(data={}, context={"attribute": attr}).save()
        return ok("Attribute deleted.")
    
class AttributeValueListCreateView(APIView):
    """
    GET     /products/attributes/<pk>/values/
    POST    /products/attributes/<pk>/values/   -> admin
    """

    def get_permissions(self):
        return [IsAdminUser()] if self.request.method == 'POST' else [AllowAny()]
    
    def get(self, request, pk):
        attr = get_object_or_404(ProductAttribute, pk=pk)
        values = attr.values.order_by('value')
        return ok("Attribute values retrieved.", data={"values": ProductAttributeValueListSerializer(values, many=True).data})

    def post(self, request, pk):
        attr = get_object_or_404(ProductAttribute, pk=pk)
        s = ProductAttributeCreateSerializer(data=request.data, context={"attribute": attr})
        s.is_valid(raise_exception=True)
        value = s.save()
        return created("Attribute value created.", data=ProductAttributeValueSerializer(value).data)


class ProductReviewListCreateView(APIView):
    """
    GET     /products/<slug>/reviews/
    POST    /products/<slug>/reviews/ -> authenticated users only
    """

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == 'POST' else[AllowAny()]
    
    def _get_product(self, slug):
        return get_object_or_404(Product, slug=slug, is_active=True)
    
    def get(self, request, slug):
        product = self._get_product(slug)
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
        return ok("Reviews retrieved.", data={"count": reviews.count(), "reviews": ProductReviewListSerializer(reviews, many=True).data})
    
    def post(self, request, slug):
        product = self._get_product(slug)
        s = ProductReviewCreateSerializer(data=request.data, context={"request": request, "product": product})
        s.is_valid(raise_exception=True)
        review = s.save()
        return created("Review submitted. It will appear after approval.", data=ProductReviewSerializer(review).data)

class ProductReviewDetailView(APIView):
    """
    GET     /products/reviews/<pk>/
    PATCH   /products/reviews/<pk>/
    DELETE  /products/reviews/<pk>/
    """

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]
    
    def _get(self, pk):
        return get_object_or_404(ProductReview, pk=pk)
    
    def get(self, request, pk):
        return ok("Review retrieved.", data=ProductReviewSerializer(self._get(pk)).data)
    
    def patch(self, request, pk):
        review = self._get(pk)
        if review.user_id != request.user.pk:
            return forbidden("You can only edit your own reviews")
        s = ProductReviewUpdateSerializer(review, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Review updated.", data=ProductReviewSerializer(s.save()).data)
    
    def delete(self, request, pk):
        review = self._get(pk)
        s = ProductReviewDeleteSerializer(data={}, context={"request": request, "review": review})
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Review deleted.")

class ProductReviewStatsView(APIView):
    """GET /products/<slug>/reviews/stats/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        return ok("Review stats retrieved.", data=ProductReviewStatsSerializer(product).data)
    
class ProductReviewHelpfulView(APIView):
    """POST /products/reviews/<pk>/helpful/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        ProductReviewHelpfulSerializer(data={}, context={"review": review}).save()
        return ok("Marked as helpful.")

class ProductReviewVerifiedView(APIView):
    """GET /products/<slug>/reviews/verified/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        reviews = product.reviews.filter(is_approved=True, is_verified_purchase=True).order_by('-created_at')
        return ok("Verified reviews retrieved.", data={"count": reviews.count(), "reviews": ProductReviewVerifiedSerializer(reviews, many=True).data})
    
class ProductReviewWithImagesView(APIView):
    """GET /products/<slug>/reviews/with-images/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
        return ok("Reviews retrieved.", data=ProductReviewWithImagesSerializer(reviews, many=True).data)

# ═════════════════════════════════════════════════════════════════════════════
# WISHLISTS
# ═════════════════════════════════════════════════════════════════════════════
class WishlistCreateView(APIView):
    """
    GET     /products/wishlists/
    POST    /products/wishlists/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlists = Wishlist.objects.filter(user=request.user).order_by('-created_at')
        return ok("Wishlists retrieved.", data={"wishlists": WishlistListSerializer(wishlists, many=True).data})
    
    def post(self, request):
        s = WishlistCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        wishlist = s.save()
        return created("Wishlist created.", data=WishlistSerializer(wishlist).data)


class WishlistDetailView(APIView):
    """
    GET     /products/wishlist/<pk>/
    PATCH   /products/wishlist/<pk>/
    DELETE  /products/wishlist/<pk>/
    """

    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        return get_object_or_404(Wishlist, pk=pk, user=user)
    
    def get(self, request, pk):
        return ok("Wishlist retrieved.", data=WishlistDetailSerializer(self._get(pk, request.user)).data)
    
    def patch(self, request, pk):
        wishlist = self._get(pk, request.user)
        s = WishlistUpdateSerializer(wishlist, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return ok("Wishlist updated.", data=WishlistSerializer(s.save()).data)
    
    def delete(self, request, pk):
        wishlist = self._get(pk, request.user)
        s = WishlistDeleteSerializer(data={}, context={"request": request, "wishlist": wishlist})
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Wishlist deleted.")
    
class WishlistItemCountView(APIView):
    """GET  /products/wishlists/item-count/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return ok("Item count retrieved.", data=WishlistItemCountSerializer(request.user).data)

class WishlistItemListCreateView(APIView):
    """
    GET     /products/wishlists/<pk>/items/
    POST    /products/wishlists/<pk>/items/
    """
    permission_classes = [IsAuthenticated]

    def _get_wishlist(self, pk, user):
        return get_object_or_404(Wishlist, pk=pk, user=user)
    
    def get(self, request, pk):
        wishlist = self._get_wishlist(pk, request.user)
        items = wishlist.items.all().order_by('-added_at')
        return ok("Wishlist items retrieved.", data={"items": WishlistItemListSerializer(items, many=True).data})
    
    def post(self, request, pk):
        wishlist = self._get_wishlist(pk, request.user)
        s = WishlistItemCreateSerializer(data=request.data, context={"wishlist": wishlist})
        s.is_valid(raise_exception=True)
        item = s.save()
        return created("Item added to wishlist.", data=WishlistItemSerializer(item).data)

class WishlistItemDeleteView(APIView):
    """DELETE /products/wishlists/<wl_pk>/items/<item_pk>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, wl_pk, item_pk):
        wishlist = get_object_or_404(Wishlist, pk=wl_pk, user=request.user)
        item     = get_object_or_404(WishlistItem, pk=item_pk, wishlist=wishlist)
        WishlistItemDeleteSerializer(data={}, context={"item": item}).save()
        return ok("Item removed from wishlist.")


class WishlistItemBulkDeleteView(APIView):
    """DELETE /products/wishlists/<pk>/items/bulk/"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)
        s = WishlistItemBulkDeleteSerializer(data=request.data, context={"wishlist": wishlist})
        s.is_valid(raise_exception=True)
        s.save()
        return ok("Items removed from wishlist")












