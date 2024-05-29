from app_analytics.views import SDKAnalyticsFlagsV2
from django.urls import re_path

app_name = "v2"

urlpatterns = [
    re_path(
        r"^analytics/flags/$", SDKAnalyticsFlagsV2.as_view(), name="analytics-flags"
    )
]
