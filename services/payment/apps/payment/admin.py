from django.contrib import admin
from .models import PaymentMethod, Transaction
admin.site.register(PaymentMethod)
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id","order_id","amount","currency","status","paid_at"]
    list_filter = ["status","currency"]
