import uuid
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from shared.responses import success_response, error_response
from .models import Order, OrderHistory
from .serializers import OrderSerializer, OrderListSerializer

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["order_number", "status"]
    ordering_fields = ["created_at", "total_amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user_id = self.request.user.id
        if self.request.user.is_staff:
            return Order.objects.prefetch_related("items", "history").all()
        return Order.objects.prefetch_related("items", "history").filter(user_id=user_id)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order = serializer.save(user_id=self.request.user.id, order_number=order_number)
        OrderHistory.objects.create(order=order, previous_status="", new_status=order.status)

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")
        valid = [c[0] for c in Order.STATUS_CHOICES]
        if new_status not in valid:
            return error_response(f"Invalid status. Valid: {valid}")
        prev = order.status
        order.status = new_status
        order.save()
        OrderHistory.objects.create(
            order=order, previous_status=prev, new_status=new_status,
            changed_by=request.user.id, note=request.data.get("note",""),
        )
        return success_response(data=OrderSerializer(order).data, message="Status updated.")

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        data = request.data
        items = data.get("items", [])
        if not items:
            return error_response("Cart is empty or no items provided.")
            
        shipping_address = data.get("shipping_address", {})
        payment_method = data.get("payment_method", "cod")
        
        from decimal import Decimal
        subtotal = Decimal(0)
        
        # Calculate subtotal natively from items to ensure sum integrity
        for item in items:
            qty = int(item.get("quantity", 1))
            price = Decimal(item.get("unit_price", 0))
            subtotal += qty * price
            
        shipping_fee = Decimal(0)
        total_amount = subtotal + shipping_fee
        
        user_id = request.user.id
        from .models import OrderItem
        from django.db import transaction
        import uuid
        
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        with transaction.atomic():
            order = Order.objects.create(
                user_id=user_id,
                order_number=order_number,
                status="pending",
                subtotal=subtotal,
                total_amount=total_amount,
                shipping_fee=shipping_fee,
                shipping_address=shipping_address,
                payment_method=payment_method
            )
            
            OrderHistory.objects.create(
                order=order, previous_status="", new_status="pending", 
                note=f"Checkout via {payment_method}"
            )
            
            order_items_to_create = []
            for item in items:
                qty = int(item.get("quantity", 1))
                price = Decimal(item.get("unit_price", 0))
                total_price = qty * price
                
                order_items_to_create.append(OrderItem(
                    order=order,
                    product_id=item.get("product_id"),
                    product_name=item.get("product_name"),
                    product_image=item.get("product_image", ""),
                    unit_price=price,
                    quantity=qty,
                    total_price=total_price
                ))
            
            OrderItem.objects.bulk_create(order_items_to_create)
            
        from shared.responses import created_response
        # Return serialized order data along with items safely
        return created_response(data=OrderSerializer(order).data, message="Đặt hàng thành công!")
