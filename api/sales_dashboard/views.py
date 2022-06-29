import json
from functools import partial

from app_analytics.influxdb_wrapper import (
    get_event_list_for_organisation,
    get_events_for_organisation,
    get_top_organisations,
)
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import ListView
from django.views.generic.edit import FormView

from edge_api.identities.events import send_migration_event
from environments.dynamodb.migrator import IdentityMigrator
from environments.identities.models import Identity
from import_export.export import full_export
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser

from .forms import EmailUsageForm, MaxAPICallsForm, MaxSeatsForm

OBJECTS_PER_PAGE = 50

MAX_MIGRATABLE_IDENTITIES_SYNC = 1000


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

        if self.request.GET.get("search"):
            search_term = self.request.GET["search"]
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(users__email__icontains=search_term)
            )

        if self.request.GET.get("filter_plan"):
            filter_plan = self.request.GET["filter_plan"]
            if filter_plan == "free":
                queryset = queryset.filter(subscription__isnull=True)
            else:
                queryset = queryset.filter(subscription__plan__icontains=filter_plan)

        # Annotate the queryset with the organisations usage for the given time periods
        # and order the queryset with it. Note: this is done as late as possible to
        # reduce the impact of the query.
        if settings.INFLUXDB_TOKEN:
            for date_range, limit in (("30d", ""), ("7d", ""), ("24h", "100")):
                key = f"num_{date_range}_calls"
                org_calls = get_top_organisations(date_range, limit)
                if org_calls:
                    whens = [When(id=k, then=Value(v)) for k, v in org_calls.items()]
                    queryset = queryset.annotate(
                        **{key: Case(*whens, default=0, output_field=IntegerField())}
                    ).order_by(f"-{key}")

        if self.request.GET.get("sort_field"):
            sort_field = self.request.GET["sort_field"]
            sort_direction = (
                "-" if self.request.GET.get("sort_direction", "ASC") == "DESC" else ""
            )
            queryset = queryset.order_by(f"{sort_direction}{sort_field}")

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
            data["search"] = search_term

        data["filter_plan"] = self.request.GET.get("filter_plan")
        data["sort_field"] = self.request.GET.get("sort_field")
        data["sort_direction"] = self.request.GET.get("sort_direction")

        return data


@staff_member_required
def organisation_info(request, organisation_id):
    organisation = get_object_or_404(Organisation, pk=organisation_id)
    template = loader.get_template("sales_dashboard/organisation.html")
    max_seats_form = MaxSeatsForm(
        {
            "max_seats": (
                0
                if (organisation.has_subscription() is False)
                else organisation.subscription.max_seats
            )
        }
    )

    max_api_calls_form = MaxAPICallsForm(
        {
            "max_api_calls": (
                50000
                if (organisation.has_subscription() is False)
                else organisation.subscription.max_api_calls
            )
        }
    )

    event_list, labels = get_event_list_for_organisation(organisation_id)

    identity_count_dict = {}
    identity_migration_status_dict = {}
    for project in organisation.projects.all():
        identity_count_dict[project.id] = Identity.objects.filter(
            environment__project=project
        ).count()
        if settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            identity_migration_status_dict[project.id] = IdentityMigrator(
                project.id
            ).migration_status.name

    context = {
        "organisation": organisation,
        "max_seats_form": max_seats_form,
        "max_api_calls_form": max_api_calls_form,
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
        "identity_count_dict": identity_count_dict,
        "identity_migration_status_dict": identity_migration_status_dict,
    }

    # If self hosted and running without an Influx DB data store, we dont want to/cant show usage
    if settings.INFLUXDB_TOKEN:
        event_list, labels = get_event_list_for_organisation(organisation_id)
        context["event_list"] = event_list
        context["traits"] = mark_safe(json.dumps(event_list["traits"]))
        context["identities"] = mark_safe(json.dumps(event_list["identities"]))
        context["flags"] = mark_safe(json.dumps(event_list["flags"]))
        context["labels"] = mark_safe(json.dumps(labels))

    return HttpResponse(template.render(context, request))


@staff_member_required
def update_seats(request, organisation_id):
    max_seats_form = MaxSeatsForm(request.POST)
    if max_seats_form.is_valid():
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        max_seats_form.save(organisation)

    return HttpResponseRedirect(reverse("sales_dashboard:index"))


@staff_member_required
def update_max_api_calls(request, organisation_id):
    max_api_calls_form = MaxAPICallsForm(request.POST)
    if max_api_calls_form.is_valid():
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        max_api_calls_form.save(organisation)

    return HttpResponseRedirect(reverse("sales_dashboard:index"))


@staff_member_required
def migrate_identities_to_edge(request, project_id):
    if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
        return HttpResponseBadRequest("DynamoDB is not enabled")
    identity_migrator = IdentityMigrator(project_id)
    if not identity_migrator.can_migrate:
        return HttpResponseBadRequest(
            "Migration is either already done or is in progress"
        )

    identity_count = Identity.objects.filter(environment__project_id=project_id).count()
    migrator_function = (
        identity_migrator.migrate
        if identity_count < MAX_MIGRATABLE_IDENTITIES_SYNC
        else partial(send_migration_event, project_id)
    )

    migrator_function()
    return HttpResponseRedirect(reverse("sales_dashboard:index"))


class EmailUsage(FormView):
    form_class = EmailUsageForm
    template_name = "sales_dashboard/email-usage.html"
    success_url = reverse_lazy("sales_dashboard:index")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@staff_member_required()
def download_org_data(request, organisation_id):
    data = full_export(organisation_id)
    response = HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=org-%d.json" % organisation_id
    )
    return response
