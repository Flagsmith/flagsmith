"""
Experimental API endpoints intended to become canonical.

These endpoints are subject to change and should not be considered stable.
Use at your own risk - breaking changes may occur without prior notice.
"""

from django.urls import path

from features.future.views import FlagAPIView

app_name = "future"

urlpatterns = [
    path(
        "environments/<str:environment_key>/features/<int:feature_id>/",
        FlagAPIView.as_view(),
        name="flag",
    ),
]
