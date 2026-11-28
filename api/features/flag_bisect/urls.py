from django.urls import path
from rest_framework_nested import routers  # type: ignore[import-untyped]

from features.flag_bisect.views import IncidentViewSet, SignalSourceView

app_name = "flag-bisect"

router = routers.DefaultRouter()
router.register(r"incidents", IncidentViewSet, basename="incidents")

urlpatterns = [
    path("signal-source/", SignalSourceView.as_view(), name="signal-source"),
    *router.urls,
]
