from django.contrib import admin
from .models import Coupon, Discount, UsageLimit
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code","name","coupon_type","is_active","starts_at","expires_at"]
admin.site.register(Discount)
admin.site.register(UsageLimit)
