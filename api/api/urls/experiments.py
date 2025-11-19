"""
Experimental API endpoints.

These endpoints are subject to change and should not be considered stable.
Use at your own risk - breaking changes may occur without prior notice.
"""

from django.urls import path

from features.feature_states.views import update_flag_v1, update_flag_v2

app_name = "experiments"

urlpatterns = [
    path(
        "environments/<int:environment_id>/update-flag-v1/",
        update_flag_v1,
        name="update-flag-v1",
    ),
    path(
        "environments/<int:environment_id>/update-flag-v2/",
        update_flag_v2,
        name="update-flag-v2",
    ),
]
