from django.db import models

# Create your models here.








# COUPON
# COUPON_USAGE



class Coupon(models.Model):
    market_id
    code 
    description
    discount_type
    discount_value
    min_purchase_amount
    max_discount_amount
    usage_limit
    usage_count
    per_user_limit
    valid_from
    valid_until
    is_active
    created_at


class CouponUsage(models.Model):
    coupon_id
    order_id
    user_id
    discount_amount
    used_at


