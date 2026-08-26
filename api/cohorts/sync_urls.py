from django.urls import path
from rest_framework.routers import SimpleRouter

from cohorts.sync_views import AmplitudeCohortSyncViewSet, MixpanelCohortSyncView

app_name = "cohort-sync"

# SimpleRouter: nothing here is browsed by a person.
router = SimpleRouter()
router.register(r"amplitude/lists", AmplitudeCohortSyncViewSet, basename="amplitude")

urlpatterns = [
    path("mixpanel/webhook/", MixpanelCohortSyncView.as_view(), name="mixpanel"),
    *router.urls,
]
