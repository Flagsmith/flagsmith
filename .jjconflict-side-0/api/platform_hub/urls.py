from django.urls import path

from platform_hub import views

app_name = "platform_hub"

urlpatterns = [
    path("summary/", views.summary_view, name="summary"),
    path("organisations/", views.organisations_view, name="organisations"),
    path("usage-trends/", views.usage_trends_view, name="usage-trends"),
    path("stale-flags/", views.stale_flags_view, name="stale-flags"),
    path("integrations/", views.integrations_view, name="integrations"),
    path(
        "release-pipelines/",
        views.release_pipelines_view,
        name="release-pipelines",
    ),
]
