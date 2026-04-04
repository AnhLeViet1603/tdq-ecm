from django.contrib import admin
from .models import Warehouse, Stock, StockHistory
admin.site.register(Warehouse)
admin.site.register(Stock)
admin.site.register(StockHistory)
