from django.urls import path

from .views import (
    ExternalResourceListCreateView,
    ExternalResourceRetrieveUpdateDestroyView,
    FeatureExternalResourceListCreateView,
    FeatureExternalResourceRetrieveUpdateDestroyView,
)

urlpatterns = [
    path(
        "external-resources/",
        ExternalResourceListCreateView.as_view(),
        name="external-resource-list-create",
    ),
    path(
        "external-resources/<int:pk>/",
        ExternalResourceRetrieveUpdateDestroyView.as_view(),
        name="external-resource-detail",
    ),
    path(
        "feature-external-resources/",
        FeatureExternalResourceListCreateView.as_view(),
        name="feature-external-resource-list-create",
    ),
    path(
        "feature-external-resources/<int:pk>/",
        FeatureExternalResourceRetrieveUpdateDestroyView.as_view(),
        name="feature-external-resource-detail",
    ),
]
