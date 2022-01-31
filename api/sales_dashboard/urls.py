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
        "organisations/<int:organisation_id>/update_max_api_calls",
        views.update_max_api_calls,
        name="update_max_api_calls",
    ),
    path(
        "email-usage/",
        staff_member_required(views.EmailUsage.as_view()),
        name="email-usage",
    ),
]
