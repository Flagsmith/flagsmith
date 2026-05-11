from django.urls import path

from integrations.flagd.views import FlagdDiagnosticsAPIView, FlagdSyncAPIView

app_name = "flagd"

urlpatterns = [
    # SDK-facing endpoints — authenticated via a server-side
    # EnvironmentAPIKey. The admin-side toggle lives under
    # /projects/<pk>/integrations/flagd/ (registered by the projects
    # app's router alongside every other integration).
    path("flags.json", FlagdSyncAPIView.as_view(), name="sync"),
    path("diagnostics.json", FlagdDiagnosticsAPIView.as_view(), name="diagnostics"),
]
