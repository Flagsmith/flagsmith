import importlib

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView

from users.views import password_reset_redirect

from . import views

urlpatterns = [
    url(r"^api/v1/", include("api.urls.deprecated", namespace="api-deprecated")),
    url(r"^api/v1/", include("api.urls.v1", namespace="api-v1")),
    url(r"^api/v2/", include("api.urls.v2", namespace="api-v2")),
    url(r"^admin/", admin.site.urls),
    url(r"^health", include("health_check.urls", namespace="health")),
    url(r"^version", views.version_info, name="version-info"),
    url(
        r"^sales-dashboard/",
        include("sales_dashboard.urls", namespace="sales_dashboard"),
    ),
    # this url is used to generate email content for the password reset workflow
    url(
        r"^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,"
        r"13}-[0-9A-Za-z]{1,20})/$",
        password_reset_redirect,
        name="password_reset_confirm",
    ),
    url(
        r"^config/project-overrides",
        views.project_overrides,
        name="project_overrides",
    ),
    path("processor/", include("task_processor.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

if settings.SAML_INSTALLED:
    urlpatterns.append(path("api/v1/auth/saml/", include("saml.urls")))

if settings.WORKFLOWS_LOGIC_INSTALLED:
    workflow_views = importlib.import_module("workflows_logic.views")
    urlpatterns.extend(
        [
            path("api/v1/features/workflows/", include("workflows_logic.urls")),
            path(
                "api/v1/environments/<str:environment_api_key>/create-change-request/",
                workflow_views.create_change_request,
                name="create-change-request",
            ),
            path(
                "api/v1/environments/<str:environment_api_key>/list-change-requests/",
                workflow_views.list_change_requests,
                name="list-change-requests",
            ),
        ]
    )

if settings.SERVE_FE_ASSETS:
    # add route to serve FE assets for any unrecognised paths
    urlpatterns.append(url(r"^.*$", views.index, name="index"))
