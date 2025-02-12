import functools
import json
import logging
import typing
from dataclasses import dataclass
from tempfile import TemporaryFile

import boto3
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, Model, Q

from edge_api.identities.export import export_edge_identity_and_overrides
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
from features.versioning.models import EnvironmentFeatureVersion
from integrations.datadog.models import DataDogConfiguration
from integrations.heap.models import HeapConfiguration
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.new_relic.models import NewRelicConfiguration
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.segment.models import SegmentConfiguration
from integrations.slack.models import SlackConfiguration, SlackEnvironment
from integrations.webhook.models import WebhookConfiguration
from metadata.models import (
    Metadata,
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from organisations.invites.models import InviteLink
from organisations.models import (
    Organisation,
    OrganisationWebhook,
    Subscription,
)
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule

logger = logging.getLogger(__name__)


class S3OrganisationExporter:
    def __init__(self, s3_client=None):
        self.s3_client = s3_client or boto3.client("s3")

    def export_to_s3(self, organisation_id: int, bucket_name: str, key: str):
        data = full_export(organisation_id)
        logger.debug("Got data export for organisation.")

        file = TemporaryFile()
        file.write(json.dumps(data, cls=DjangoJSONEncoder).encode("utf-8"))
        file.seek(0)
        logger.debug("Wrote data export to temporary file.")

        self.s3_client.upload_fileobj(file, bucket_name, key)
        logger.info("Finished writing data export to s3.")


def full_export(organisation_id: int) -> typing.List[dict]:
    return [
        *export_organisation(organisation_id),
        *export_projects(organisation_id),
        *export_environments(organisation_id),
        *export_identities(organisation_id),
        *export_features(organisation_id),
        *export_metadata(organisation_id),
        *export_edge_identities(organisation_id),
    ]


def export_organisation(organisation_id: int) -> typing.List[dict]:
    """
    Serialize an organisation and all its related objects.
    """
    return _export_entities(
        _EntityExportConfig(Organisation, Q(id=organisation_id)),
        _EntityExportConfig(InviteLink, Q(organisation__id=organisation_id)),
        _EntityExportConfig(OrganisationWebhook, Q(organisation__id=organisation_id)),
        _EntityExportConfig(Subscription, Q(organisation__id=organisation_id)),
    )


def export_metadata(organisation_id: int) -> typing.List[dict]:
    return _export_entities(
        _EntityExportConfig(MetadataField, Q(organisation__id=organisation_id)),
        _EntityExportConfig(
            MetadataModelField, Q(field__organisation__id=organisation_id)
        ),
        _EntityExportConfig(
            MetadataModelFieldRequirement,
            Q(model_field__field__organisation__id=organisation_id),
        ),
        _EntityExportConfig(
            Metadata, Q(model_field__field__organisation__id=organisation_id)
        ),
    )


def export_projects(organisation_id: int) -> typing.List[dict]:
    default_filter = Q(project__organisation__id=organisation_id)

    return _export_entities(
        _EntityExportConfig(Project, Q(organisation__id=organisation_id)),
        _EntityExportConfig(
            Segment, Q(project__organisation__id=organisation_id, id=F("version_of"))
        ),
        _EntityExportConfig(
            SegmentRule,
            Q(
                segment__project__organisation__id=organisation_id,
                segment_id=F("segment__version_of"),
            )
            | Q(
                rule__segment__project__organisation__id=organisation_id,
                rule__segment_id=F("rule__segment__version_of"),
            ),
        ),
        _EntityExportConfig(
            Condition,
            Q(
                rule__segment__project__organisation__id=organisation_id,
                rule__segment_id=F("rule__segment__version_of"),
            )
            | Q(
                rule__rule__segment__project__organisation__id=organisation_id,
                rule__rule__segment_id=F("rule__rule__segment__version_of"),
            ),
        ),
        _EntityExportConfig(Tag, default_filter),
        _EntityExportConfig(DataDogConfiguration, default_filter),
        _EntityExportConfig(NewRelicConfiguration, default_filter),
        _EntityExportConfig(SlackConfiguration, default_filter),
    )


def export_environments(organisation_id: int) -> typing.List[dict]:
    default_filter = Q(environment__project__organisation__id=organisation_id)

    return _export_entities(
        _EntityExportConfig(Environment, Q(project__organisation__id=organisation_id)),
        _EntityExportConfig(EnvironmentAPIKey, default_filter),
        _EntityExportConfig(Webhook, default_filter),
        _EntityExportConfig(HeapConfiguration, default_filter),
        _EntityExportConfig(MixpanelConfiguration, default_filter),
        _EntityExportConfig(SegmentConfiguration, default_filter),
        _EntityExportConfig(RudderstackConfiguration, default_filter),
        _EntityExportConfig(WebhookConfiguration, default_filter),
        _EntityExportConfig(SlackEnvironment, default_filter),
    )


def export_identities(organisation_id: int) -> typing.List[dict]:
    traits = _export_entities(
        _EntityExportConfig(
            Trait,
            Q(
                identity__environment__project__organisation__id=organisation_id,
                identity__environment__project__enable_dynamo_db=False,
            ),
        ),
    )

    identities = _export_entities(
        _EntityExportConfig(
            Identity,
            Q(
                environment__project__organisation__id=organisation_id,
                environment__project__enable_dynamo_db=False,
            ),
        ),
    )

    # We export the traits first so that we take a 'snapshot' before exporting the
    # identities, otherwise we end up with issues where new traits are created for new
    # identities during the export process and the identity doesn't exist in the import.
    # We then need to reverse the order so that the identities are imported first.
    return [*identities, *traits]


def export_edge_identities(organisation_id: int) -> typing.List[dict]:
    identities = []
    traits = []
    identity_overrides = []
    for environment in Environment.objects.filter(
        project__organisation__id=organisation_id, project__enable_dynamo_db=True
    ):
        exported_identities, exported_traits, exported_overrides = (
            export_edge_identity_and_overrides(environment.api_key)
        )
        identities.extend(exported_identities)
        traits.extend(exported_traits)
        identity_overrides.extend(exported_overrides)

    return [*identities, *traits, *identity_overrides]


def export_features(organisation_id: int) -> typing.List[dict]:
    """
    Export all features and related entities, except ChangeRequests.
    """

    feature_states = []
    for feature_state in _export_entities(
        _EntityExportConfig(
            FeatureState, Q(feature__project__organisation__id=organisation_id)
        )
    ):
        # Since we're not exporting any user objects, we want to exclude change
        # requests from the export. This means, however, that we need to remove the
        # FK dependency on the change request from the FeatureState before export.
        feature_state["fields"]["change_request"] = None
        feature_states.append(feature_state)

    return (
        _export_entities(
            _EntityExportConfig(
                Feature,
                Q(project__organisation__id=organisation_id),
                exclude_fields=["owners", "group_owners"],
            ),
            _EntityExportConfig(
                EnvironmentFeatureVersion,
                Q(feature__project__organisation__id=organisation_id),
                exclude_fields=["created_by", "published_by"],
            ),
            _EntityExportConfig(
                MultivariateFeatureOption,
                Q(feature__project__organisation__id=organisation_id),
            ),
            _EntityExportConfig(
                FeatureSegment,
                Q(feature__project__organisation__id=organisation_id),
            ),
        )
        + feature_states  # feature states need to be imported in correct order
        + _export_entities(
            _EntityExportConfig(
                FeatureStateValue,
                Q(feature_state__feature__project__organisation__id=organisation_id),
            ),
            _EntityExportConfig(
                MultivariateFeatureStateValue,
                Q(feature_state__feature__project__organisation__id=organisation_id),
            ),
        )
    )


@dataclass
class _EntityExportConfig:
    model_class: type(Model)
    qs_filter: Q
    exclude_fields: typing.List[str] = None


def _export_entities(
    *export_configs: _EntityExportConfig,
) -> typing.List[dict]:
    entities = []
    for config in export_configs:
        args = ("python", config.model_class.objects.filter(config.qs_filter))
        kwargs = {}
        if config.exclude_fields:
            kwargs["fields"] = [
                f.name
                for f in config.model_class._meta.get_fields()
                if f.name not in config.exclude_fields
            ]
        entities.extend(_serialize_natural(*args, **kwargs))
    return entities


_serialize_natural = functools.partial(
    serializers.serialize,
    use_natural_primary_keys=True,
    use_natural_foreign_keys=True,
)
