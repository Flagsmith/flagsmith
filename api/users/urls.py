from django.conf import settings
from django.urls import path, re_path

from organisations.invites.views import (
    join_organisation_from_email,
    join_organisation_from_link,
)

from .views import AdminInitView, InitialConfigurationView

app_name = "users"

urlpatterns = [
    path(
        "join/<str:hash>/", join_organisation_from_email, name="user-join-organisation"
    ),
    path("config/init/", InitialConfigurationView.as_view(), name="config-init"),
    path(
        "join/link/<str:hash>/",
        join_organisation_from_link,
        name="user-join-organisation-link",
    ),
]

if settings.ALLOW_ADMIN_INITIATION_VIA_URL:  # pragme: no cover
    urlpatterns.insert(0, re_path(r"^init/", AdminInitView.as_view()))
