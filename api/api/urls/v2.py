from app_analytics.views import SDKAnalyticsFlagsV2
from django.conf.urls import url

app_name = "v2"

urlpatterns = [
    url(r"^analytics/flags/$", SDKAnalyticsFlagsV2.as_view(), name="analytics-flags")
]
