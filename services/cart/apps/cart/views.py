from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from shared.responses import success_response, error_response, not_found_response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_or_create_cart(self, user_id):
        cart, _ = Cart.objects.get_or_create(user_id=user_id)
        return cart

    @action(detail=False, methods=["get"], url_path="me")
    def my_cart(self, request):
        cart = self._get_or_create_cart(request.user.id)
        return success_response(data=CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="add")
    def add_item(self, request):
        cart = self._get_or_create_cart(request.user.id)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        item, created = CartItem.objects.get_or_create(
            cart=cart, product_id=data["product_id"],
            defaults=data,
        )
        if not created:
            item.quantity += data.get("quantity", 1)
            item.save()
        return success_response(data=CartSerializer(cart).data, message="Item added to cart.")

    @action(detail=False, methods=["delete"], url_path="remove/(?P<item_id>[^/.]+)")
    def remove_item(self, request, item_id=None):
        cart = self._get_or_create_cart(request.user.id)
        try:
            CartItem.objects.get(id=item_id, cart=cart).delete()
        except CartItem.DoesNotExist:
            return not_found_response("Cart item not found.")
        return success_response(data=CartSerializer(cart).data, message="Item removed.")

    @action(detail=False, methods=["patch"], url_path="update/(?P<item_id>[^/.]+)")
    def update_item(self, request, item_id=None):
        cart = self._get_or_create_cart(request.user.id)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return not_found_response("Cart item not found.")

        quantity = request.data.get("quantity")
        if quantity is None:
            return error_response("Quantity is required.", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantity = int(quantity)
        except ValueError:
            return error_response("Quantity must be an integer.", status_code=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()

        return success_response(data=CartSerializer(cart).data, message="Item updated.")

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, request):
        cart = self._get_or_create_cart(request.user.id)
        cart.items.all().delete()
        return success_response(message="Cart cleared.")
