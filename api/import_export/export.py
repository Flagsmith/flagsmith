import functools
import itertools
import typing
from dataclasses import dataclass

from django.core import serializers
from django.db.models import Model, Q

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
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


def full_export(organisation_id: int) -> typing.List[dict]:
    return [
        *export_organisation(organisation_id),
        *export_projects(organisation_id),
        *export_environments(organisation_id),
        *export_identities(organisation_id),
        *export_features(organisation_id),
    ]


def export_organisation(organisation_id: int) -> typing.List[dict]:
    """
    Serialize an organisation and all its related objects.
    """
    return _export_entities(
        [
            _EntityExportConfig(Organisation, Q(id=organisation_id)),
            _EntityExportConfig(InviteLink, Q(organisation__id=organisation_id)),
            _EntityExportConfig(
                OrganisationWebhook, Q(organisation__id=organisation_id)
            ),
            _EntityExportConfig(Subscription, Q(organisation__id=organisation_id)),
        ]
    )


def export_projects(organisation_id: int) -> typing.List[dict]:
    default_filter = Q(project__organisation__id=organisation_id)

    return _export_entities(
        [
            _EntityExportConfig(Project, Q(organisation__id=organisation_id)),
            _EntityExportConfig(Segment, default_filter),
            _EntityExportConfig(
                SegmentRule,
                Q(segment__project__organisation__id=organisation_id)
                | Q(rule__segment__project__organisation__id=organisation_id),
            ),
            _EntityExportConfig(
                Condition,
                Q(rule__segment__project__organisation__id=organisation_id)
                | Q(rule__rule__segment__project__organisation__id=organisation_id),
            ),
            _EntityExportConfig(Tag, default_filter),
            _EntityExportConfig(DataDogConfiguration, default_filter),
            _EntityExportConfig(NewRelicConfiguration, default_filter),
            _EntityExportConfig(SlackConfiguration, default_filter),
        ]
    )


def export_environments(organisation_id: int) -> typing.List[dict]:
    default_filter = Q(environment__project__organisation__id=organisation_id)

    return _export_entities(
        [
            _EntityExportConfig(
                Environment, Q(project__organisation__id=organisation_id)
            ),
            _EntityExportConfig(EnvironmentAPIKey, default_filter),
            _EntityExportConfig(Webhook, default_filter),
            _EntityExportConfig(HeapConfiguration, default_filter),
            _EntityExportConfig(MixpanelConfiguration, default_filter),
            _EntityExportConfig(SegmentConfiguration, default_filter),
            _EntityExportConfig(RudderstackConfiguration, default_filter),
            _EntityExportConfig(WebhookConfiguration, default_filter),
            _EntityExportConfig(SlackEnvironment, default_filter),
        ]
    )


def export_identities(organisation_id: int) -> typing.List[dict]:
    return _export_entities(
        [
            _EntityExportConfig(
                Identity, Q(environment__project__organisation__id=organisation_id)
            ),
            _EntityExportConfig(
                Trait,
                Q(identity__environment__project__organisation__id=organisation_id),
            ),
        ]
    )


def export_features(organisation_id: int) -> typing.List[dict]:
    """
    Export all features and related entities (including ChangeRequests)
    """

    return _export_entities(
        [
            _EntityExportConfig(Feature, Q(project__organisation__id=organisation_id)),
            _EntityExportConfig(
                MultivariateFeatureOption,
                Q(feature__project__organisation__id=organisation_id),
            ),
            _EntityExportConfig(
                FeatureSegment, Q(feature__project__organisation__id=organisation_id)
            ),
            _EntityExportConfig(
                ChangeRequest, Q(environment__project__organisation__id=organisation_id)
            ),
            _EntityExportConfig(
                FeatureState, Q(feature__project__organisation__id=organisation_id)
            ),
            _EntityExportConfig(
                FeatureStateValue,
                Q(feature_state__feature__project__organisation__id=organisation_id),
            ),
            _EntityExportConfig(
                MultivariateFeatureStateValue,
                Q(feature_state__feature__project__organisation__id=organisation_id),
            ),
        ]
    )


@dataclass
class _EntityExportConfig:
    model_class: type(Model)
    qs_filter: Q


def _export_entities(
    export_configs: typing.List[_EntityExportConfig],
) -> typing.List[dict]:
    return list(
        itertools.chain(
            *[
                _serialize_natural(
                    "python",
                    export_config.model_class.objects.filter(export_config.qs_filter),
                )
                for export_config in export_configs
            ]
        )
    )


_serialize_natural = functools.partial(
    serializers.serialize,
    use_natural_primary_keys=True,
    use_natural_foreign_keys=True,
)
