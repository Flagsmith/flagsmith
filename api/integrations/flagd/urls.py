from django.urls import path

from integrations.flagd.views import FlagdSyncAPIView

app_name = "flagd"

urlpatterns = [
    path("flags.json", FlagdSyncAPIView.as_view(), name="sync"),
]
