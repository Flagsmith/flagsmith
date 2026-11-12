from rest_framework.routers import DefaultRouter

from cohorts.views import CohortSyncKeyViewSet, CohortViewSet

app_name = "cohorts"

router = DefaultRouter()
router.register(r"sync-keys", CohortSyncKeyViewSet, basename="sync-keys")
router.register(r"", CohortViewSet, basename="cohorts")

urlpatterns = router.urls
