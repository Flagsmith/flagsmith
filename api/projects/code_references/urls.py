from django.urls import path

from . import views

app_name = "code_references"

urlpatterns = [
    path(
        "projects/<int:project_pk>/code-references/",
        views.CodeReferenceCreateAPIView.as_view(),
        name="code_reference_create",
    ),
]
