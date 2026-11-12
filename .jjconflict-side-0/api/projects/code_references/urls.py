from django.urls import path

from projects.code_references import views

app_name = "code_references"

urlpatterns = [
    path(
        "projects/<int:project_pk>/code-references/",
        views.FeatureFlagCodeReferencesScanCreateAPIView.as_view(),
        name="code_reference_create",
    ),
    path(
        "projects/<int:project_pk>/features/<int:feature_pk>/code-references/",
        views.FeatureFlagCodeReferenceDetailAPIView.as_view(),
        name="feature_code_reference_detail",
    ),
]
