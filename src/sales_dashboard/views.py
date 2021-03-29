import json

from app_analytics.influxdb_wrapper import (
    get_event_list_for_organisation,
    get_events_for_organisation,
    get_top_organisations,
)
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.utils.safestring import mark_safe
from django.views.generic import ListView

from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser

OBJECTS_PER_PAGE = 50


class OrganisationList(ListView):
    model = Organisation
    paginate_by = OBJECTS_PER_PAGE
    template_name = "sales_dashboard/home.html"

    def get_queryset(self):
        queryset = Organisation.objects.annotate(
            num_projects=Count("projects", distinct=True),
            num_users=Count("users", distinct=True),
            num_features=Count("projects__features", distinct=True),
            num_segments=Count("projects__segments", distinct=True),
        )

        # Annotate the queryset with the organisations usage for the given time periods
        # and order the queryset with it.
        if settings.INFLUXDB_TOKEN:
            for date_range, limit in (("30d", ""), ("7d", ""), ("24h", "100")):
                key = f"num_{date_range}_calls"
                org_calls = get_top_organisations(date_range, limit)
                if org_calls:
                    whens = [When(id=k, then=Value(v)) for k, v in org_calls.items()]
                    queryset = queryset.annotate(
                        **{key: Case(*whens, default=0, output_field=IntegerField())}
                    ).order_by(f"-{key}")

        if "search" in self.request.GET:
            search_term = self.request.GET["search"]
            queryset = queryset.filter(name__icontains=search_term)

        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        if "search" in self.request.GET:
            search_term = self.request.GET["search"]
            projects = Project.objects.all().filter(name__icontains=search_term)[:20]
            data["projects"] = projects

            users = FFAdminUser.objects.all().filter(
                Q(last_name__icontains=search_term) | Q(email__icontains=search_term)
            )[:20]
            data["users"] = users

        return data


@staff_member_required
def organisation_info(request, organisation_id):
    organisation = get_object_or_404(Organisation, pk=organisation_id)
    event_list, labels = get_event_list_for_organisation(organisation_id)
    template = loader.get_template("sales_dashboard/organisation.html")
    context = {
        "organisation": organisation,
        "event_list": event_list,
        "traits": mark_safe(json.dumps(event_list["traits"])),
        "identities": mark_safe(json.dumps(event_list["identities"])),
        "flags": mark_safe(json.dumps(event_list["flags"])),
        "labels": mark_safe(json.dumps(labels)),
        "api_calls": {
            # TODO: this could probably be reduced to a single influx request
            #  rather than 3
            range_: get_events_for_organisation(organisation_id, date_range=range_)
            for range_ in ("24h", "7d", "30d")
        },
    }

    return HttpResponse(template.render(context, request))
