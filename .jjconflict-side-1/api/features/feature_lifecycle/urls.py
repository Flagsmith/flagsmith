from django.urls import path

from features.feature_lifecycle import views

app_name = "feature-lifecycle"

urlpatterns = [
    path(
        "environments/<int:environment_pk>/feature-lifecycle-counts/",
        views.FeatureLifecycleCountsAPIView.as_view(),
        name="feature-lifecycle-counts",
    ),
]
