from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, StockViewSet, StockHistoryViewSet

router = DefaultRouter()
router.register("warehouses", WarehouseViewSet, basename="warehouses")
router.register("stock-history", StockHistoryViewSet, basename="stock-history")
router.register("", StockViewSet, basename="stocks")

urlpatterns = router.urls
