# 5. ORDERS APP (32 serializers)
# Orders:
#
# OrderSerializer - Views basic order information
# OrderCreateSerializer - Creates new order from cart (checkout)
# OrderUpdateSerializer - Updates order details (limited fields)
# OrderDeleteSerializer - Cancels order with reason
# OrderDetailSerializer - Shows complete order with items, addresses, payment, shipping
# OrderListSerializer - Lists orders with minimal data for performance
# OrderBuyerListSerializer - Shows buyer's order history
# OrderSellerListSerializer - Shows seller's orders to fulfill
# OrderStatusUpdateSerializer - Updates order status (seller/admin)
# OrderCancelSerializer - Cancels order with cancellation reason
# OrderTrackingSerializer - Shows order tracking information
# OrderHistorySerializer - Returns order history with date filters
# OrderSearchSerializer - Searches orders by order number, product, etc.
# OrderStatsSerializer - Returns order statistics and analytics
# OrderInvoiceSerializer - Generates order invoice/receipt
#
# Order Items:
#
# OrderItemSerializer - Views single order item details
# OrderItemListSerializer - Lists all items in an order
# OrderItemDetailSerializer - Shows order item with full product details
#
# Order Addresses:
#
# OrderAddressSerializer - Shows order shipping and billing addresses
# OrderShippingAddressSerializer - Shows only shipping address
# OrderBillingAddressSerializer - Shows only billing address
#
# Order Shipping:
#
# OrderShippingSerializer - Views order shipping details
# OrderShippingCreateSerializer - Adds shipping information to order
# OrderShippingUpdateSerializer - Updates tracking number and carrier
# OrderShippingTrackingSerializer - Shows detailed shipment tracking
# ShippingMethodSerializer - Views shipping method details
# ShippingMethodCreateSerializer - Creates new shipping method (seller/admin)
# ShippingMethodUpdateSerializer - Updates shipping method details
# ShippingMethodDeleteSerializer - Deletes shipping method
# ShippingMethodListSerializer - Lists available shipping methods
# CalculateShippingCostSerializer - Calculates shipping cost for address
# TrackingUpdateSerializer - Updates order tracking status