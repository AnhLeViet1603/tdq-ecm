from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from shared.responses import success_response, error_response
from .models import Warehouse, Stock, StockHistory
from .serializers import WarehouseSerializer, StockSerializer, StockHistorySerializer

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.filter(is_active=True)
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related("warehouse").all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["product_sku"]

    @action(detail=True, methods=["post"], url_path="adjust")
    def adjust(self, request, pk=None):
        stock = self.get_object()
        qty_change = int(request.data.get("quantity_change", 0))
        reason = request.data.get("reason", "adjustment")
        before = stock.quantity
        stock.quantity = max(0, before + qty_change)
        stock.save()
        StockHistory.objects.create(
            stock=stock, quantity_change=qty_change,
            quantity_before=before, quantity_after=stock.quantity,
            reason=reason, performed_by=getattr(request.user, "id", None),
        )
        return success_response(data=StockSerializer(stock).data, message="Stock adjusted.")

class StockHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockHistory.objects.select_related("stock").all()
    serializer_class = StockHistorySerializer
    permission_classes = [IsAuthenticated]
