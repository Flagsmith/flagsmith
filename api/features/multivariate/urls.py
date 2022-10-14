from django.urls import path

from features.multivariate.views import get_mv_feature_option_by_uuid

app_name = "multivariate"

urlpatterns = [
    path(
        "options/get-by-uuid/<uuid:uuid>/",
        get_mv_feature_option_by_uuid,
        name="get-mv-feature-option-by-uuid",
    ),
]
