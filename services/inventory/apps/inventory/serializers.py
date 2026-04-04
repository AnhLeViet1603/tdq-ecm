from rest_framework import serializers
from .models import Warehouse, Stock, StockHistory

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"

class StockSerializer(serializers.ModelSerializer):
    available = serializers.IntegerField(read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    class Meta:
        model = Stock
        fields = "__all__"

class StockHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHistory
        fields = "__all__"
