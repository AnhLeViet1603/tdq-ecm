from django.contrib import admin
from .models import Carrier, Shipment, TrackingLog
admin.site.register(Carrier)
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ["tracking_number","carrier","status","order_id","actual_delivery"]
    list_filter = ["status"]
admin.site.register(TrackingLog)
