from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from . import views

app_name = "sales_dashboard"


urlpatterns = [
    path("", staff_member_required(views.OrganisationList.as_view()), name="index"),
    path(
        "organisations/<int:organisation_id>",
        views.organisation_info,
        name="organisation_info",
    ),
    path(
        "organisations/<int:organisation_id>/update_seats",
        views.update_seats,
        name="update_seats",
    ),
    path(
        "organisations/<int:project_id>/migrate_identities",
        views.migrate_identities_to_edge,
        name="migrate_identities",
    ),
    path(
        "organisations/<int:organisation_id>/update_max_api_calls",
        views.update_max_api_calls,
        name="update_max_api_calls",
    ),
    path(
        "email-usage/",
        staff_member_required(views.EmailUsage.as_view()),
        name="email-usage",
    ),
    path(
        "organisations/<int:organisation_id>/download_org_data",
        views.download_org_data,
        name="download-org-data",
    ),
]
