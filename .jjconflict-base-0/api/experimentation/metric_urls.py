from rest_framework.routers import DefaultRouter

from experimentation.views import MetricViewSet

app_name = "experiment_metrics"

router = DefaultRouter()
router.register(r"", MetricViewSet, basename="metrics")

urlpatterns = router.urls
