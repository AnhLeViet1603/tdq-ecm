from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from shared.responses import success_response, error_response
from .models import Carrier, Shipment, TrackingLog
from .serializers import CarrierSerializer, ShipmentSerializer, TrackingLogSerializer

class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.filter(is_active=True)
    serializer_class = CarrierSerializer
    permission_classes = [IsAuthenticated]

class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.select_related("carrier").prefetch_related("logs").all()
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["tracking_number","status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        order_id = self.request.query_params.get("order_id")
        if order_id:
            qs = qs.filter(order_id=order_id)
        return qs

    @action(detail=True, methods=["post"], url_path="add-log")
    def add_log(self, request, pk=None):
        shipment = self.get_object()
        data = request.data
        log = TrackingLog.objects.create(
            shipment=shipment,
            status=data.get("status", shipment.status),
            location=data.get("location",""),
            description=data.get("description",""),
            timestamp=data.get("timestamp", timezone.now()),
        )
        shipment.status = log.status
        shipment.save()
        return success_response(data=ShipmentSerializer(shipment).data, message="Tracking log added.")
