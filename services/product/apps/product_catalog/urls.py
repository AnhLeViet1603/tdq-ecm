from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, AttributeViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories",  CategoryViewSet,  basename="categories")
router.register("attributes",  AttributeViewSet, basename="attributes")
router.register("",            ProductViewSet,   basename="products")

urlpatterns = router.urls
