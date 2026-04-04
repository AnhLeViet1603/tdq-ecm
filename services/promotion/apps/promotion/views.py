from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from shared.responses import success_response, error_response
from .models import Coupon
from .serializers import CouponSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.select_related("discount","usage_limit").all()
    serializer_class = CouponSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["code","name"]

    def get_permissions(self):
        if self.action == "validate":
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=["post"], url_path="validate")
    def validate(self, request):
        code = request.data.get("code","").upper()
        try:
            coupon = Coupon.objects.select_related("discount","usage_limit").get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return error_response("Coupon not found or inactive.", status_code=404)
        now = timezone.now()
        if coupon.starts_at > now:
            return error_response("Coupon is not active yet.")
        if coupon.expires_at and coupon.expires_at < now:
            return error_response("Coupon has expired.")
        if hasattr(coupon,"usage_limit") and coupon.usage_limit.is_exhausted:
            return error_response("Coupon usage limit reached.")
        return success_response(data=CouponSerializer(coupon).data, message="Coupon is valid.")
