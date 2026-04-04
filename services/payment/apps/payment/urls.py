from rest_framework.routers import DefaultRouter
from .views import PaymentMethodViewSet, TransactionViewSet
router = DefaultRouter()
router.register("methods", PaymentMethodViewSet, basename="payment-methods")
router.register("transactions", TransactionViewSet, basename="transactions")
urlpatterns = router.urls
