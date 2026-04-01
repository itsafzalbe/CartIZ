# User Cards:
#
# UserCardSerializer - Views card details with masked card number
# UserCardListSerializer - Lists all user payment cards
# UserCardCreateSerializer - Adds new payment card to account
# UserCardUpdateSerializer - Updates card details (not card number)
# UserCardDeleteSerializer - Removes payment card from account
# SetDefaultCardSerializer - Sets card as default payment method
# CardBalanceSerializer - Views current card balance
# CardBalanceDepositSerializer - Adds money to card balance
# CardBalanceWithdrawSerializer - Withdraws money from card balance
# Card Transactions:
#
# CardTransactionSerializer - Views single transaction details
# CardTransactionListSerializer - Lists all card transactions with filters
# CardTransactionHistorySerializer - Shows complete transaction history for a card


# 6. PAYMENTS APP (20 serializers)
# Payments:
#
# PaymentSerializer - Views payment transaction details
# PaymentCreateSerializer - Processes payment for order
# PaymentListSerializer - Lists all user payments
# PaymentDetailSerializer - Shows complete payment information
# PaymentVerifySerializer - Verifies payment status
# PaymentStatusSerializer - Checks current payment status
# PaymentReceiptSerializer - Generates payment receipt
#
# Refunds:
#
# RefundSerializer - Views refund details
# RefundRequestSerializer - Requests refund for order (buyer)
# RefundCreateSerializer - Creates refund transaction
# RefundUpdateSerializer - Updates refund status
# RefundListSerializer - Lists all refunds with filters
# RefundDetailSerializer - Shows complete refund information
# RefundApproveSerializer - Approves refund request (seller)
# RefundRejectSerializer - Rejects refund request with reason
# RefundBuyerListSerializer - Shows buyer's refund requests
# RefundSellerListSerializer - Shows seller's refund requests to process
#
# Payment Stats:
#
# PaymentStatsSerializer - Returns payment statistics and analytics
# RefundStatsSerializer - Returns refund statistics
# TransactionHistorySerializer - Shows complete transaction history (payments + refunds)