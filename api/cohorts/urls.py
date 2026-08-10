from rest_framework.routers import DefaultRouter

from cohorts.views import CohortViewSet

app_name = "cohorts"

router = DefaultRouter()
router.register(r"", CohortViewSet, basename="cohorts")

urlpatterns = router.urls
