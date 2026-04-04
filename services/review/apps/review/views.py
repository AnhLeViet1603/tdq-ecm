from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from shared.responses import success_response
from .models import Review, ReviewMedia
from .serializers import ReviewSerializer, ReviewMediaSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.prefetch_related("media").all()
    serializer_class = ReviewSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["rating","created_at","helpful_count"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["list","retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id, is_approved=True)
        return qs

    def create(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        user_id = request.user.id
        user_name = request.user.full_name
        
        if not product_id:
            from shared.responses import error_response
            return error_response("product_id is required.")
            
        # Prevent duplicate reviews if order_id is not used
        # if Review.objects.filter(product_id=product_id, user_id=user_id).exists():
        #     from shared.responses import error_response
        #     return error_response("Bạn đã đánh giá sản phẩm này rồi.")

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            from shared.responses import error_response
            return error_response("Invalid data", errors=serializer.errors)
            
        self.perform_create(serializer)
        
        from shared.responses import created_response
        return created_response(data=serializer.data, message="Gửi đánh giá thành công.")

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id, user_name=self.request.user.full_name)

    @action(detail=True, methods=["post"], url_path="helpful")
    def helpful(self, request, pk=None):
        review = self.get_object()
        review.helpful_count += 1
        review.save()
        return success_response(data={"helpful_count": review.helpful_count})
