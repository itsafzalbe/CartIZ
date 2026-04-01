# 7. PRODUCTS APP (108 serializers)
# Categories:
#
# CategorySerializer - Views basic category information
# CategoryCreateSerializer - Creates new product category (admin)
# CategoryUpdateSerializer - Updates category details
# CategoryDeleteSerializer - Deletes category
# CategoryListSerializer - Lists all categories with minimal data
# CategoryTreeSerializer - Shows category hierarchy with subcategories
# CategoryDetailSerializer - Shows category with products and subcategories
# CategoryProductCountSerializer - Shows category with product count
#
# Products:
#
# ProductSerializer - Views basic product information
# ProductCreateSerializer - Creates new product (seller)
# ProductUpdateSerializer - Updates product details (seller)
# ProductDeleteSerializer - Deletes or deactivates product
# ProductDetailSerializer - Shows complete product with images, variants, reviews
# ProductListSerializer - Lists products with optimized minimal data
# ProductCardSerializer - Shows product card for grid/list view
# ProductSearchSerializer - Returns product search results
# ProductSellerSerializer - Shows product from seller's management view
# ProductPublicSerializer - Shows product as buyers see it
# ProductQuickViewSerializer - Shows product quick view modal data
# ProductRelatedSerializer - Returns related/similar products
# ProductStatsSerializer - Shows product performance statistics
# ProductFeaturedSerializer - Returns featured products for homepage
# ProductBestSellerSerializer - Shows best-selling products
# ProductNewArrivalSerializer - Shows newly added products
# ProductTrendingSerializer - Returns currently trending products
# ProductTopRatedSerializer - Shows highest-rated products
#
# Product Stock:
#
# ProductStockSerializer - Views product stock information
# ProductStockUpdateSerializer - Updates product quantity (seller)
# ProductLowStockSerializer - Shows products with low stock alerts
#
# Product Images:
#
# ProductImageSerializer - Views single product image
# ProductImageCreateSerializer - Uploads new product image
# ProductImageUpdateSerializer - Updates image details (alt text, order)
# ProductImageDeleteSerializer - Deletes product image
# ProductImageListSerializer - Lists all images for a product
# SetPrimaryImageSerializer - Sets primary product image
# ProductImageBulkUploadSerializer - Uploads multiple images at once
#
# Product Variants:
#
# ProductVariantSerializer - Views product variant details
# ProductVariantCreateSerializer - Creates new product variant
# ProductVariantUpdateSerializer - Updates variant details
# ProductVariantDeleteSerializer - Deletes product variant
# ProductVariantListSerializer - Lists all variants for a product
# ProductVariantStockSerializer - Shows variant stock information
#
# Product Attributes:
#
# ProductAttributeSerializer - Views attribute (Color, Size, etc.)
# ProductAttributeCreateSerializer - Creates new attribute type (admin)
# ProductAttributeUpdateSerializer - Updates attribute details
# ProductAttributeDeleteSerializer - Deletes attribute
# ProductAttributeListSerializer - Lists all available attributes
# ProductAttributeValueSerializer - Views attribute value (Red, Large, etc.)
# ProductAttributeValueCreateSerializer - Creates new attribute value
# ProductAttributeValueListSerializer - Lists values for an attribute
#
# Product Reviews:
#
# ProductReviewSerializer - Views product review details
# ProductReviewCreateSerializer - Creates new product review (verified purchase)
# ProductReviewUpdateSerializer - Edits existing review
# ProductReviewDeleteSerializer - Deletes review
# ProductReviewListSerializer - Lists all reviews for a product
# ProductReviewStatsSerializer - Shows rating breakdown (5-star distribution)
# ProductReviewHelpfulSerializer - Marks review as helpful/unhelpful
# ProductReviewVerifiedSerializer - Shows only verified purchase reviews
# ProductReviewWithImagesSerializer - Shows reviews with customer photos
#
# Wishlist:
#
# WishlistSerializer - Views user's wishlist
# WishlistCreateSerializer - Creates new wishlist
# WishlistUpdateSerializer - Updates wishlist name/settings
# WishlistDeleteSerializer - Deletes wishlist
# WishlistListSerializer - Lists all user wishlists
# WishlistDetailSerializer - Shows wishlist with all items
# WishlistItemCountSerializer - Returns number of items in wishlist
#
# Wishlist Items:
#
# WishlistItemSerializer - Views wishlist item details
# WishlistItemCreateSerializer - Adds product to wishlist
# WishlistItemDeleteSerializer - Removes item from wishlist
# WishlistItemListSerializer - Lists all items in wishlist
# WishlistItemDetailSerializer - Shows wishlist item with full product details
# WishlistItemBulkDeleteSerializer - Removes multiple items from wishlist
#
# Product Discovery:
#
# FeaturedProductsSerializer - Returns featured/promoted products
# TrendingProductsSerializer - Shows currently trending products
# NewArrivalsSerializer - Returns recently added products
# BestSellersSerializer - Shows top-selling products
# SimilarProductsSerializer - Returns products similar to current product
# FrequentlyBoughtTogetherSerializer - Shows products often bought together
# YouMayAlsoLikeSerializer - Returns personalized product recommendations
# RecommendedProductsSerializer - Shows recommended products based on user history
#
# Product Browsing:
#
# CategoryBrowseSerializer - Shows category page with products and subcategories
# CategoryProductListSerializer - Lists products in a category with filters
# SubcategoryListSerializer - Shows subcategories within a category
# CategoryBreadcrumbSerializer - Generates category navigation breadcrumb
# PopularCategoriesSerializer - Shows most popular categories
# CategoryWithTopProductsSerializer - Shows category with its top products
# ProductListPageSerializer - Returns complete product listing page data
#
# Product Filtering:
#
# ProductFilterSerializer - Applies filters to product list (price, rating, etc.)
# PriceRangeFilterSerializer - Filters products by price range
# RatingFilterSerializer - Filters products by minimum rating
# BrandFilterSerializer - Filters products by brand/market
# AvailabilityFilterSerializer - Filters by in-stock/out-of-stock
# AttributeFilterSerializer - Filters by product attributes (color, size)
# SortOptionsSerializer - Returns available sorting options
# AvailableFiltersSerializer - Shows all available filters for current results
# ActiveFiltersSerializer - Shows currently applied filters
# FilterCountSerializer - Returns product count for each filter option
# PriceRangeSerializer - Shows min/max price for current results
# ProductGridSerializer - Returns products formatted for grid view
#
# Personalization:
#
# PersonalizedFeedSerializer - Shows personalized product feed for user
# RecentlyViewedSerializer - Returns user's recently viewed products
# ViewHistorySerializer - Shows user's complete browsing history
# ForYouSerializer - Returns "For You" personalized recommendations
# BasedOnYourInterestsSerializer - Shows products based on user interests
# BecauseYouViewedSerializer - Shows "Because you viewed X" recommendations
#
# Product Comparison:
#
# ProductCompareSerializer - Compares multiple products side-by-side
# ProductCompareAddSerializer - Adds product to comparison list
# ProductCompareListSerializer - Shows all products in comparison list