from rest_framework.routers import DefaultRouter

from experimentation.views import WarehouseConnectionViewSet

app_name = "experimentation"

router = DefaultRouter()
router.register(r"", WarehouseConnectionViewSet, basename="warehouse-connections")

urlpatterns = router.urls
