from rest_framework import serializers
from .models import Order, OrderItem, OrderHistory

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        exclude = ["order"]

class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        exclude = ["order"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    history = OrderHistorySerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = "__all__"

class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id","order_number","status","total_amount","created_at"]
