import json

from app_analytics.influxdb_wrapper import (
    get_event_list_for_organisation,
    get_events_for_organisation,
)
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.utils.safestring import mark_safe
from django.views.generic import ListView

from organisations.models import Organisation, UserOrganisation
from projects.models import Project
from users.models import FFAdminUser

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
    }

    return HttpResponse(template.render(context, request))
