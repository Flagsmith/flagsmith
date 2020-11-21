import json

from analytics.influxdb_wrapper import (
    get_event_list_for_organisation,
    get_events_for_organisation,
)
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from organisations.models import Organisation
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

OBJECTS_PER_PAGE = 50


class OrganisationList(ListView):
    model = Organisation
    paginate_by = OBJECTS_PER_PAGE
    template_name = "sales_dashboard/home.html"

    def get_queryset(self):
        if "search" in self.request.GET:
            search_term = self.request.GET["search"]
            organisations = (
                Organisation.objects.annotate(projects_num=Count("projects"))
                .annotate(user_num=Count("users"))
                .all()
                .filter(name__icontains=search_term)
            )
        else:
            organisations = (
                Organisation.objects.annotate(projects_num=Count("projects"))
                .annotate(user_num=Count("users"))
                .all()
            )

        list_of_organisations = []

        for organisation in organisations:
            list_of_organisations.append(
                {
                    "id": organisation.id,
                    "name": organisation.name,
                    "date_registered": organisation.created_date,
                    "projects": organisation.projects_num,
                    "users": organisation.user_num,
                    "flags": sum(
                        [
                            project.features.count()
                            for project in organisation.projects.all()
                        ]
                    ),
                    "segments": sum(
                        [
                            project.segments.count()
                            for project in organisation.projects.all()
                        ]
                    ),
                }
            )
        return list_of_organisations


@staff_member_required
def organisation_info(request, organisation_id):
    organisation = get_object_or_404(Organisation, pk=organisation_id)
    event_list, labels = get_event_list_for_organisation(organisation_id)
    template = loader.get_template("sales_dashboard/organisation.html")
    context = {
        "organisation": organisation,
        "event_list": mark_safe(json.dumps(event_list)),
        "labels": mark_safe(json.dumps(labels)),
    }

    return HttpResponse(template.render(context, request))
