from django.urls import re_path

from app_analytics.views import SDKAnalyticsFlagsV2, SDKEvaluationDataView

app_name = "v2"

urlpatterns = [
    re_path(
        r"^analytics/flags/$", SDKAnalyticsFlagsV2.as_view(), name="analytics-flags"
    ),
    re_path(
        r"^analytics/evaluations/$",
        SDKEvaluationDataView.as_view(),
        name="analytics-evaluations",
    ),
]
