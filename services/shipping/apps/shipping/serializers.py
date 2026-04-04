from rest_framework import serializers
from .models import Carrier, Shipment, TrackingLog

class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        exclude = ["api_key"]

class TrackingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingLog
        exclude = ["shipment"]

class ShipmentSerializer(serializers.ModelSerializer):
    logs = TrackingLogSerializer(many=True, read_only=True)
    carrier_name = serializers.CharField(source="carrier.name", read_only=True)
    class Meta:
        model = Shipment
        fields = "__all__"
