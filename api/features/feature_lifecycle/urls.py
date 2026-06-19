from django.urls import path

from features.feature_lifecycle import views

urlpatterns = [
    path(
        "environments/<int:environment_pk>/feature-lifecycle-counts/",
        views.FeatureLifecycleCountsAPIView.as_view(),
        name="feature-lifecycle-counts",
    ),
]
