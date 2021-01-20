from django.conf import settings
from django.conf.urls import url
from django.urls import path

from .views import AdminInitView
from organisations.invites.views import (
    join_organisation_from_email,
    join_organisation_from_link,
)

app_name = "users"

urlpatterns = [
    path(
        "join/<str:hash>/", join_organisation_from_email, name="user-join-organisation"
    ),
    path(
        "join/link/<str:hash>/",
        join_organisation_from_link,
        name="user-join-organisation-link",
    ),
]

if settings.ALLOW_ADMIN_INITIATION_VIA_URL:
    urlpatterns.insert(0, url(r"init/", AdminInitView.as_view()))
