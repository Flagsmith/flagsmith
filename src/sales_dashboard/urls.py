from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required

from . import views

app_name = "sales_dashboard"


urlpatterns = [
    path("", staff_member_required(views.OrganisationList.as_view()), name="index"),
    path(
        "organisations/<int:organisation_id>",
        views.organisation_info,
        name="organistation_info",
    ),
]
