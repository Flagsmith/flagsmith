"""
Experimental API endpoints.

These endpoints are subject to change and should not be considered stable.
Use at your own risk - breaking changes may occur without prior notice.
"""

from django.urls import path

from features.feature_states.views import (
    delete_segment_override,
    update_flag_option_a,
    update_flag_option_b,
)

app_name = "experiments"

urlpatterns = [
    path(
        "environments/<str:environment_key>/update-flag-v1/",
        update_flag_option_a,
        name="update-flag-option-a",
    ),
    path(
        "environments/<str:environment_key>/update-flag-v2/",
        update_flag_option_b,
        name="update-flag-option-b",
    ),
    path(
        "environments/<str:environment_key>/delete-segment-override/",
        delete_segment_override,
        name="delete-segment-override",
    ),
]
