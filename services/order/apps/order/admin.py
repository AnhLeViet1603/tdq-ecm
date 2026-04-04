from django.contrib import admin
from .models import Order, OrderItem, OrderHistory
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number","status","total_amount","user_id","created_at"]
    list_filter = ["status"]
admin.site.register(OrderItem)
admin.site.register(OrderHistory)
