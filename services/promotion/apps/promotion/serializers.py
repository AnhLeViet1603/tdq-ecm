from rest_framework import serializers
from .models import Coupon, Discount, UsageLimit

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        exclude = ["coupon"]

class UsageLimitSerializer(serializers.ModelSerializer):
    is_exhausted = serializers.BooleanField(read_only=True)
    class Meta:
        model = UsageLimit
        exclude = ["coupon"]

class CouponSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True)
    usage_limit = UsageLimitSerializer(read_only=True)
    class Meta:
        model = Coupon
        fields = "__all__"
