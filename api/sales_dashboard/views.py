import json

from app_analytics.influxdb_wrapper import (
    get_event_list_for_organisation,
    get_events_for_organisation,
)
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, F, Q, Value
from django.db.models.functions import Greatest
from django.http import (
    HttpRequest,
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

from environments.dynamodb.migrator import IdentityMigrator
from environments.identities.models import Identity
from import_export.export import full_export
from organisations.chargebee.tasks import update_chargebee_cache
from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from organisations.tasks import (
    update_organisation_subscription_information_cache,
    update_organisation_subscription_information_influx_cache,
)

from .forms import (
    EmailUsageForm,
    EndTrialForm,
    MaxAPICallsForm,
    MaxSeatsForm,
    StartTrialForm,
)

OBJECTS_PER_PAGE = 50
DEFAULT_ORGANISATION_SORT = "subscription_information_cache__api_calls_30d"
DEFAULT_ORGANISATION_SORT_DIRECTION = "DESC"


class OrganisationList(ListView):
    model = Organisation
    paginate_by = OBJECTS_PER_PAGE
    template_name = "sales_dashboard/home.html"

    def get_queryset(self):
        queryset = Organisation.objects.annotate(
            num_projects=Count("projects", distinct=True),
            num_users=Count("users", distinct=True),
            num_features=Count("projects__features", distinct=True),
            overage=Greatest(
                Value(0),
                F("subscription_information_cache__api_calls_30d")
                - F("subscription_information_cache__allowed_30d_api_calls"),
            ),
        ).select_related("subscription", "subscription_information_cache")

        if self.request.GET.get("search"):
            search_term = self.request.GET["search"]
            queryset = queryset.filter(
                Q(name__icontains=search_term)
                | Q(users__email__icontains=search_term)
                | Q(subscription__subscription_id=search_term)
            )

        if self.request.GET.get("filter_plan"):
            filter_plan = self.request.GET["filter_plan"]
            queryset = queryset.filter(subscription__plan__icontains=filter_plan)

        sort_field = self.request.GET.get("sort_field") or DEFAULT_ORGANISATION_SORT
        sort_direction = (
            self.request.GET.get("sort_direction")
            or DEFAULT_ORGANISATION_SORT_DIRECTION
        )
        queryset = (
            queryset.order_by(sort_field)
            if sort_direction == "ASC"
            else queryset.order_by(F(sort_field).desc(nulls_last=True))
        )

        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["search"] = self.request.GET.get("search", "")
        data["filter_plan"] = self.request.GET.get("filter_plan")
        data["sort_field"] = self.request.GET.get("sort_field")
        data["sort_direction"] = self.request.GET.get("sort_direction")

        # Use the most recent "influx_updated_at" in
        # OrganisationSubscriptionInformationCache object to determine
        # when the caches were last updated.
        try:
            subscription_information_caches_influx_updated_at = (
                OrganisationSubscriptionInformationCache.objects.order_by(
                    F("influx_updated_at").desc(nulls_last=True)
                )
                .first()
                .influx_updated_at.strftime("%H:%M:%S %d/%m/%Y")
            )

        except AttributeError:
            subscription_information_caches_influx_updated_at = None

        data["subscription_information_caches_influx_updated_at"] = (
            subscription_information_caches_influx_updated_at
        )

        return data


@staff_member_required
def organisation_info(request, organisation_id):
    organisation = get_object_or_404(
        Organisation.objects.select_related("subscription"), pk=organisation_id
    )
    template = loader.get_template("sales_dashboard/organisation.html")
    subscription_metadata = organisation.subscription.get_subscription_metadata()

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
        "max_api_calls": subscription_metadata.api_calls,
        "max_seats": subscription_metadata.seats,
        "max_projects": subscription_metadata.projects,
        "chargebee_email": subscription_metadata.chargebee_email,
        "identity_count_dict": identity_count_dict,
        "identity_migration_status_dict": identity_migration_status_dict,
    }

    # If self-hosted and running without an Influx DB data store, we don't want to/cant show usage
    if settings.INFLUXDB_TOKEN:
        date_range = request.GET.get("date_range", "180d")
        context["date_range"] = date_range

        event_list, labels = get_event_list_for_organisation(
            organisation_id, date_range
        )
        context["event_list"] = event_list
        context["traits"] = mark_safe(json.dumps(event_list["traits"]))
        context["identities"] = mark_safe(json.dumps(event_list["identities"]))
        context["flags"] = mark_safe(json.dumps(event_list["flags"]))
        context["environment_documents"] = mark_safe(
            json.dumps(event_list["environment-document"])
        )
        context["labels"] = mark_safe(json.dumps(labels))
        context["api_calls"] = {
            # TODO: this could probably be reduced to a single influx request
            #  rather than 3
            range_: get_events_for_organisation(organisation_id, date_range=range_)
            for range_ in ("24h", "7d", "30d")
        }

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
def organisation_start_trial(
    request: HttpRequest, organisation_id: int
) -> HttpResponse:
    start_trial_form = StartTrialForm(request.POST)
    if start_trial_form.is_valid():
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        start_trial_form.save(organisation)

    return HttpResponseRedirect(
        reverse(
            "sales_dashboard:organisation_info",
            kwargs={"organisation_id": organisation_id},
        )
    )


@staff_member_required
def organisation_end_trial(request: HttpRequest, organisation_id: int) -> HttpResponse:
    end_trial_form = EndTrialForm(request.POST)
    if end_trial_form.is_valid():
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        end_trial_form.save(organisation)

    return HttpResponseRedirect(
        reverse(
            "sales_dashboard:organisation_info",
            kwargs={"organisation_id": organisation_id},
        )
    )


@staff_member_required
def migrate_identities_to_edge(request, project_id):
    if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
        return HttpResponseBadRequest("DynamoDB is not enabled")

    identity_migrator = IdentityMigrator(project_id)
    if not identity_migrator.can_migrate:
        return HttpResponseBadRequest(
            "Migration is either already done or is in progress"
        )
    identity_migrator.trigger_migration()

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


@staff_member_required()
def trigger_update_organisation_subscription_information_influx_cache(request):
    update_organisation_subscription_information_influx_cache.delay()
    return HttpResponseRedirect(reverse("sales_dashboard:index"))


@staff_member_required()
def trigger_update_organisation_subscription_information_cache(request):
    update_organisation_subscription_information_cache.delay()
    return HttpResponseRedirect(reverse("sales_dashboard:index"))


@staff_member_required()
def trigger_update_chargebee_caches(request):
    update_chargebee_cache.delay()
    return HttpResponseRedirect(reverse("sales_dashboard:index"))
