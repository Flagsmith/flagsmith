import functools
import typing

from django.core import serializers
from django.db.models import Q

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.multivariate.models import MultivariateFeatureOption
from features.workflows.core.models import ChangeRequest
from integrations.datadog.models import DataDogConfiguration
from integrations.heap.models import HeapConfiguration
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.new_relic.models import NewRelicConfiguration
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.segment.models import SegmentConfiguration
from integrations.slack.models import SlackConfiguration, SlackEnvironment
from integrations.webhook.models import WebhookConfiguration
from organisations.invites.models import InviteLink
from organisations.models import (
    Organisation,
    OrganisationWebhook,
    Subscription,
)
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule

serialize_natural = functools.partial(
    serializers.serialize, use_natural_primary_keys=True, use_natural_foreign_keys=True
)


def export_organisation(organisation_id: int) -> typing.List[dict]:
    organisation_model = Organisation.objects.get(id=organisation_id)

    data = []

    # add the organisation
    data += serialize_natural("python", [organisation_model])
    data += serialize_natural(
        "python", InviteLink.objects.filter(organisation=organisation_model)
    )
    data += serialize_natural(
        "python", OrganisationWebhook.objects.filter(organisation=organisation_model)
    )
    data += serialize_natural(
        "python", Subscription.objects.filter(organisation=organisation_model)
    )

    # add projects and their related models
    data += serialize_natural(
        "python", Project.objects.filter(organisation=organisation_model)
    )
    data += serialize_natural(
        "python",
        Segment.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        SegmentRule.objects.filter(
            Q(segment__project__organisation=organisation_model)
            | Q(rule__segment__project__organisation=organisation_model)
        ),
    )
    data += serialize_natural(
        "python",
        Condition.objects.filter(
            Q(rule__segment__project__organisation=organisation_model)
            | Q(rule__rule__segment__project__organisation=organisation_model)
        ),
    )
    data += serialize_natural(
        "python", Tag.objects.filter(project__organisation=organisation_model)
    )
    data += serialize_natural(
        "python",
        DataDogConfiguration.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        NewRelicConfiguration.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        SlackConfiguration.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        SlackEnvironment.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    # TODO: integrations

    # add environments and their related models
    data += serialize_natural(
        "python",
        Environment.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        EnvironmentAPIKey.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        Webhook.objects.filter(environment__project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        HeapConfiguration.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        MixpanelConfiguration.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        SegmentConfiguration.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        RudderstackConfiguration.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        WebhookConfiguration.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )
    # TODO: integrations

    # add features and their related_models
    data += serialize_natural(
        "python",
        Feature.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        MultivariateFeatureOption.objects.filter(
            feature__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        FeatureSegment.objects.filter(
            feature__project__organisation=organisation_model
        ),
    )

    # add identities and traits
    data += serialize_natural(
        "python",
        Identity.objects.filter(
            environment__project__organisation=organisation_model
        ).select_related("environment"),
    )
    data += serialize_natural(
        "python",
        Trait.objects.filter(
            identity__environment__project__organisation=organisation_model
        ).select_related("identity", "identity__environment"),
    )

    # add change requests
    data += serialize_natural(
        "python",
        ChangeRequest.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )

    # add the feature states now that we should have all the related entities
    data += serialize_natural(
        "python",
        FeatureState.objects.filter(feature__project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        FeatureStateValue.objects.filter(
            feature_state__feature__project__organisation=organisation_model
        ),
    )

    return data
