import os

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path

from users.views import password_reset_redirect

from . import views

urlpatterns = [
    url(r"^api/v1/", include("api.urls.deprecated", namespace="api-deprecated")),
    url(r"^api/v1/", include("api.urls.v1", namespace="api-v1")),
    url(r"^admin/", admin.site.urls),
    url(r"^health", include("health_check.urls", namespace="health")),
    url(r"^version", views.version_info),
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
    path("", views.index, name="index"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

if settings.ENVIRONMENT == "saas" and os.path.exists(
    os.path.join(settings.BASE_DIR, "saml")
):
    urlpatterns += [
        path("api/v1/auth/saml/", include("saml.urls")),
    ]

urlpatterns += [
    # Catch all for subfolder views on the front end
    # Note: must be after all other URL paths
    url(r"^.*/$", views.index, name="index"),
]
