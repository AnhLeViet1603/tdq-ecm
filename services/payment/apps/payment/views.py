from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from shared.responses import success_response
from .models import PaymentMethod, Transaction
from .serializers import PaymentMethodSerializer, TransactionSerializer

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PaymentMethod.objects.filter(user_id=self.request.user.id, is_active=True)
    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-created_at"]
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user_id=self.request.user.id)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            from shared.responses import error_response
            return error_response("Invalid data", errors=serializer.errors)
        self.perform_create(serializer)
        from shared.responses import created_response
        return created_response(data=serializer.data, message="Giao dịch đã được ghi nhận.")

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)
