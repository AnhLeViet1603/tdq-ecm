from rest_framework.routers import DefaultRouter
from .views import CarrierViewSet, ShipmentViewSet
router = DefaultRouter()
router.register("carriers", CarrierViewSet, basename="carriers")
router.register("", ShipmentViewSet, basename="shipments")
urlpatterns = router.urls
