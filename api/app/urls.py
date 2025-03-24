import importlib

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import TemplateView

from users.views import password_reset_redirect

from . import views

urlpatterns = [
    re_path(r"^health/liveness/?", views.liveness),
    re_path(r"^health/readiness/?", include("health_check.urls")),
    path("processor/", include("task_processor.urls")),
]

if not settings.TASK_PROCESSOR_MODE:
    urlpatterns += [
        re_path(
            r"^api/v1/", include("api.urls.deprecated", namespace="api-deprecated")
        ),
        re_path(r"^api/v1/", include("api.urls.v1", namespace="api-v1")),
        re_path(r"^api/v2/", include("api.urls.v2", namespace="api-v2")),
        re_path(r"^admin/", admin.site.urls),
        re_path(r"^health", include("health_check.urls", namespace="health")),
        # Aptible health checks must be on /healthcheck and cannot redirect
        # see https://www.aptible.com/docs/core-concepts/apps/connecting-to-apps/app-endpoints/https-endpoints/health-checks
        path("healthcheck", include("health_check.urls", namespace="aptible")),
        re_path(r"^version", views.version_info, name="version-info"),
        re_path(
            r"^sales-dashboard/",
            include("sales_dashboard.urls", namespace="sales_dashboard"),
        ),
        # this url is used to generate email content for the password reset workflow
        re_path(
            r"^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,"
            r"13}-[0-9A-Za-z]{1,20})/$",
            password_reset_redirect,
            name="password_reset_confirm",
        ),
        re_path(
            r"^config/project-overrides",
            views.project_overrides,
            name="project_overrides",
        ),
        path(
            "robots.txt",
            TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        ),
    ]

if settings.DEBUG:
    urlpatterns = [
        re_path(r"^__debug__/", include("debug_toolbar.urls")),
    ] + urlpatterns

if settings.SAML_INSTALLED:  # pragma: no cover
    urlpatterns += [
        path("api/v1/auth/saml/", include("saml.urls")),
    ]

if settings.WORKFLOWS_LOGIC_INSTALLED:  # pragma: no cover
    workflow_views = importlib.import_module("workflows_logic.views")
    urlpatterns += [
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


if settings.SERVE_FE_ASSETS:  # pragma: no cover
    # add route to serve FE assets for any unrecognised paths
    urlpatterns.append(re_path(r"^.*$", views.index, name="index"))
