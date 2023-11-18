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
        "organisations/<int:organisation_id>/organisation_start_trial",
        views.organisation_start_trial,
        name="organisation_start_trial",
    ),
    path(
        "organisations/<int:organisation_id>/organisation_end_trial",
        views.organisation_end_trial,
        name="organisation_end_trial",
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
    path(
        "update-organisation-subscription-information-influx-cache",
        views.trigger_update_organisation_subscription_information_influx_cache,
        name="update-organisation-subscription-information-influx-cache",
    ),
    path(
        "update-organisation-subscription-information-cache",
        views.trigger_update_organisation_subscription_information_cache,
        name="update-organisation-subscription-information-cache",
    ),
    path(
        "update-chargebee-cache",
        views.trigger_update_chargebee_caches,
        name="update-chargebee-cache",
    ),
]
