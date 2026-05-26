"""
products/urls.py
=================
Include in your project urls.py with:
  path('products/', include('apps.products.urls')),

Full URL map
─────────────────────────────────────────────────────────────────
CATEGORIES
  GET     /products/categories/                       list root categories
  POST    /products/categories/                       create category (admin)
  GET     /products/categories/tree/                  full nested tree
  GET     /products/categories/popular/               most popular categories
  GET     /products/categories/with-products/         categories + top 4 products
  GET     /products/categories/<pk>/                  category detail
  PATCH   /products/categories/<pk>/                  update category (admin)
  DELETE  /products/categories/<pk>/                  soft-delete (admin)
  GET     /products/categories/<pk>/browse/           category browse page
  GET     /products/categories/<pk>/breadcrumb/       navigation breadcrumb
  GET     /products/categories/<pk>/subcategories/    list subcategories
  GET     /products/categories/<pk>/products/         products in category

PRODUCTS — CRUD
  GET     /products/                                  list all products (filtered)
  POST    /products/                                  create product (seller)
  GET     /products/my-products/                      seller's own products
  GET     /products/my-products/low-stock/            seller's low stock products
  GET     /products/<slug>/                           public product detail
  PATCH   /products/<slug>/                           update product (owner)
  DELETE  /products/<slug>/                           soft-delete (owner)
  GET     /products/<slug>/quick-view/                quick view modal
  GET     /products/<slug>/stats/                     product stats (seller)

STOCK
  GET     /products/<slug>/stock/                     stock info (seller)
  PATCH   /products/<slug>/stock/                     update stock (seller)

IMAGES
  GET     /products/<slug>/images/                    list images
  POST    /products/<slug>/images/                    upload image (seller)
  POST    /products/<slug>/images/bulk/               bulk upload (seller)
  PATCH   /products/images/<pk>/                      update image (seller)
  DELETE  /products/images/<pk>/                      delete image (seller)
  PATCH   /products/images/<pk>/set-primary/          set primary image (seller)

VARIANTS
  GET     /products/<slug>/variants/                  list variants
  POST    /products/<slug>/variants/                  create variant (seller)
  GET     /products/variants/<pk>/                    variant detail
  PATCH   /products/variants/<pk>/                    update variant (seller)
  DELETE  /products/variants/<pk>/                    deactivate variant (seller)
  GET     /products/variants/<pk>/stock/              variant stock (seller)

ATTRIBUTES
  GET     /products/attributes/                       list all attributes
  POST    /products/attributes/                       create attribute (admin)
  GET     /products/attributes/<pk>/                  attribute detail
  PATCH   /products/attributes/<pk>/                  update attribute (admin)
  DELETE  /products/attributes/<pk>/                  delete attribute (admin)
  GET     /products/attributes/<pk>/values/           list attribute values
  POST    /products/attributes/<pk>/values/           create attribute value (admin)

REVIEWS
  GET     /products/<slug>/reviews/                   list approved reviews
  POST    /products/<slug>/reviews/                   create review (auth)
  GET     /products/<slug>/reviews/stats/             rating breakdown
  GET     /products/<slug>/reviews/verified/          verified purchase reviews
  GET     /products/<slug>/reviews/with-images/       reviews with photos
  GET     /products/reviews/<pk>/                     review detail
  PATCH   /products/reviews/<pk>/                     edit own review
  DELETE  /products/reviews/<pk>/                     delete own review
  POST    /products/reviews/<pk>/helpful/             mark review as helpful

WISHLISTS
  GET     /products/wishlists/                        list user wishlists
  POST    /products/wishlists/                        create wishlist
  GET     /products/wishlists/item-count/             total item count (badge)
  GET     /products/wishlists/<pk>/                   wishlist detail
  PATCH   /products/wishlists/<pk>/                   update wishlist
  DELETE  /products/wishlists/<pk>/                   delete wishlist
  GET     /products/wishlists/<pk>/items/             list items in wishlist
  POST    /products/wishlists/<pk>/items/             add item to wishlist
  DELETE  /products/wishlists/<pk>/items/<item_pk>/   remove single item
  DELETE  /products/wishlists/<pk>/items/bulk/        bulk remove items

DISCOVERY
  GET     /products/featured/                         featured products
  GET     /products/trending/                         trending products
  GET     /products/new-arrivals/                     new arrivals
  GET     /products/best-sellers/                     best-selling products
  GET     /products/top-rated/                        highest-rated products
  GET     /products/<slug>/similar/                   similar products
  GET     /products/<slug>/frequently-bought/         frequently bought together
  GET     /products/<slug>/you-may-also-like/         you may also like
  GET     /products/<slug>/because-you-viewed/        because you viewed

PERSONALIZATION (auth required)
  GET     /products/feed/                             personalised feed
  GET     /products/recently-viewed/                  recently viewed
  GET     /products/for-you/                          for you
  GET     /products/interests/                        based on your interests
  GET     /products/recommended/                      recommended products

BROWSING & FILTERING
  GET     /products/search/                           full text search (?q=)
  GET     /products/grid/                             grid view with filters
  GET     /products/filters/available/                available filters
  GET     /products/sort-options/                     sort options

COMPARISON
  POST    /products/compare/                          compare products (list of IDs)
  POST    /products/compare/add/                      validate add to comparison
─────────────────────────────────────────────────────────────────
"""

from django.urls import path

from .views import *

urlpatterns = [

    # ── Categories — static paths first ──────────────────────────────────────
    path('categories/tree/',            CategoryTreeView.as_view(),             name='category-tree'),
    path('categories/popular/',         PopularCategoriesView.as_view(),        name='category-popular'),
    path('categories/with-products/',   CategoryWithTopProductsView.as_view(),  name='category-with-products'),
    path('categories/',                 CategoryListCreateView.as_view(),        name='category-list'),
    path('categories/<int:pk>/',                CategoryDetailView.as_view(),       name='category-detail'),
    path('categories/<int:pk>/browse/',         CategoryBrowseView.as_view(),       name='category-browse'),
    path('categories/<int:pk>/breadcrumb/',     CategoryBreadcrumbView.as_view(),   name='category-breadcrumb'),
    path('categories/<int:pk>/subcategories/',  SubcategoryListView.as_view(),      name='category-subcategories'),
    path('categories/<int:pk>/products/',       CategoryProductListView.as_view(),  name='category-products'),

    # ── Seller's own products — before <slug> to avoid conflict ──────────────
    path('my-products/',                SellerProductListView.as_view(),        name='my-products'),
    path('my-products/low-stock/',      LowStockProductsView.as_view(),         name='my-products-low-stock'),

    # ── Discovery — static paths before <slug> ───────────────────────────────
    path('featured/',                   FeaturedProductsView.as_view(),         name='product-featured'),
    path('trending/',                   TrendingProductsView.as_view(),         name='product-trending'),
    path('new-arrivals/',               NewArrivalsView.as_view(),              name='product-new-arrivals'),
    path('best-sellers/',               BestSellersView.as_view(),              name='product-best-sellers'),
    path('top-rated/',                  TopRatedProductsView.as_view(),         name='product-top-rated'),
    path('recommended/',                RecommendedProductsView.as_view(),      name='product-recommended'),

    # ── Browsing & filtering ──────────────────────────────────────────────────
    path('search/',                     ProductSearchView.as_view(),            name='product-search'),
    path('grid/',                       ProductGridView.as_view(),              name='product-grid'),
    path('filters/available/',          AvailableFiltersView.as_view(),         name='product-filters'),
    path('sort-options/',               SortOptionsView.as_view(),              name='product-sort-options'),

    # ── Personalisation ───────────────────────────────────────────────────────
    path('feed/',                       PersonalizedFeedView.as_view(),         name='product-feed'),
    path('recently-viewed/',            RecentlyViewedView.as_view(),           name='product-recently-viewed'),
    path('for-you/',                    ForYouView.as_view(),                   name='product-for-you'),
    path('interests/',                  BasedOnYourInterestsView.as_view(),     name='product-interests'),

    # ── Wishlists — static paths before <pk> ─────────────────────────────────
    path('wishlists/item-count/',       WishlistItemCountView.as_view(),        name='wishlist-item-count'),
    path('wishlists/',                  WishlistListCreateView.as_view(),       name='wishlist-list'),
    path('wishlists/<int:pk>/',                         WishlistDetailView.as_view(),           name='wishlist-detail'),
    path('wishlists/<int:pk>/items/',                   WishlistItemListCreateView.as_view(),   name='wishlist-items'),
    path('wishlists/<int:pk>/items/bulk/',               WishlistItemBulkDeleteView.as_view(),   name='wishlist-items-bulk-delete'),
    path('wishlists/<int:wl_pk>/items/<int:item_pk>/',  WishlistItemDeleteView.as_view(),       name='wishlist-item-delete'),

    # ── Attributes ────────────────────────────────────────────────────────────
    path('attributes/',                         AttributeListCreateView.as_view(),      name='attribute-list'),
    path('attributes/<int:pk>/',                AttributeDetailView.as_view(),          name='attribute-detail'),
    path('attributes/<int:pk>/values/',         AttributeValueListCreateView.as_view(), name='attribute-values'),

    # ── Images (by PK — no slug needed) ──────────────────────────────────────
    path('images/<int:pk>/',                    ProductImageDetailView.as_view(),       name='product-image-detail'),
    path('images/<int:pk>/set-primary/',        SetPrimaryImageView.as_view(),          name='product-image-set-primary'),

    # ── Variants (by PK) ──────────────────────────────────────────────────────
    path('variants/<int:pk>/',                  ProductVariantDetailView.as_view(),     name='product-variant-detail'),
    path('variants/<int:pk>/stock/',            ProductVariantStockView.as_view(),      name='product-variant-stock'),

    # ── Reviews (by PK) ───────────────────────────────────────────────────────
    path('reviews/<int:pk>/',                   ProductReviewDetailView.as_view(),      name='product-review-detail'),
    path('reviews/<int:pk>/helpful/',           ProductReviewHelpfulView.as_view(),     name='product-review-helpful'),

    # ── Comparison ────────────────────────────────────────────────────────────
    path('compare/',                    ProductCompareView.as_view(),           name='product-compare'),
    path('compare/add/',                ProductCompareAddView.as_view(),        name='product-compare-add'),

    # ── Product list / create ─────────────────────────────────────────────────
    path('',                            ProductListCreateView.as_view(),        name='product-list'),

    # ── <slug> based routes — must come after all static paths ───────────────
    path('<slug:slug>/',                        ProductDetailView.as_view(),            name='product-detail'),
    path('<slug:slug>/quick-view/',             ProductQuickView.as_view(),             name='product-quick-view'),
    path('<slug:slug>/stats/',                  ProductStatsView.as_view(),             name='product-stats'),
    path('<slug:slug>/stock/',                  ProductStockView.as_view(),             name='product-stock'),
    path('<slug:slug>/images/',                 ProductImageListCreateView.as_view(),   name='product-images'),
    path('<slug:slug>/images/bulk/',            ProductImageBulkUploadView.as_view(),   name='product-images-bulk'),
    path('<slug:slug>/variants/',               ProductVariantListCreateView.as_view(), name='product-variants'),
    path('<slug:slug>/reviews/',                ProductReviewListCreateView.as_view(),  name='product-reviews'),
    path('<slug:slug>/reviews/stats/',          ProductReviewStatsView.as_view(),       name='product-reviews-stats'),
    path('<slug:slug>/reviews/verified/',       ProductReviewVerifiedView.as_view(),    name='product-reviews-verified'),
    path('<slug:slug>/reviews/with-images/',    ProductReviewWithImagesView.as_view(),  name='product-reviews-with-images'),
    path('<slug:slug>/similar/',                SimilarProductsView.as_view(),          name='product-similar'),
    path('<slug:slug>/frequently-bought/',      FrequentlyBoughtTogetherView.as_view(), name='product-frequently-bought'),
    path('<slug:slug>/you-may-also-like/',      YouMayAlsoLikeView.as_view(),           name='product-you-may-also-like'),
    path('<slug:slug>/because-you-viewed/',     BecauseYouViewedView.as_view(),         name='product-because-you-viewed'),
]