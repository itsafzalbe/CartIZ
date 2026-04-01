# 2. CART APP (22 serializers)
# Cart:
#
# CartSerializer - Views cart with all items and basic details
# CartDetailSerializer - Returns cart with full product details for each item
# CartSummarySerializer - Shows cart totals (subtotal, tax, shipping, total)
# CartItemCountSerializer - Returns number of items in cart for badge display
#
# Cart Items:
#
# CartItemSerializer - Views single cart item details
# CartItemCreateSerializer - Adds product to cart with quantity validation
# CartItemUpdateSerializer - Updates cart item quantity
# CartItemDeleteSerializer - Removes item from cart
# CartItemListSerializer - Lists all items in cart with minimal data
# CartItemDetailSerializer - Shows cart item with full product and variant details
# AddToCartSerializer - Adds product to cart with stock validation
# UpdateCartQuantitySerializer - Changes quantity for existing cart item
# ClearCartSerializer - Empties entire cart
# CartItemBulkUpdateSerializer - Updates multiple cart items at once
# CartItemBulkDeleteSerializer - Removes multiple items from cart
# MoveToWishlistSerializer - Moves cart item to wishlist
# SaveForLaterSerializer - Saves cart item for later purchase
# MoveToCartSerializer - Moves wishlist/saved item to cart
#
# Cart Operations:
#
# ApplyCouponToCartSerializer - Applies discount coupon to cart
# RemoveCouponFromCartSerializer - Removes applied coupon from cart
# CalculateShippingForCartSerializer - Calculates shipping cost for cart items
# CartValidationSerializer - Validates cart before checkout (stock, prices, availability)