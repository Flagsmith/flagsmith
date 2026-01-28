import functools
import json
import logging
import typing
from collections.abc import Iterator
from dataclasses import dataclass

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
from import_export.utils import S3MultipartUploadWriter
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
    def __init__(self, s3_client: typing.Any = None) -> None:
        self.s3_client = s3_client or boto3.client("s3")

    def export_to_s3(
        self,
        organisation_id: int,
        bucket_name: str,
        key: str,
    ) -> None:
        data = full_export(organisation_id)
        logger.debug("Starting streaming export for organisation.")

        with S3MultipartUploadWriter(self.s3_client, bucket_name, key) as writer:
            writer.write(b"[")
            first = True
            for item in data:
                if not first:
                    writer.write(b",")
                first = False
                writer.write(json.dumps(item, cls=DjangoJSONEncoder).encode("utf-8"))
            writer.write(b"]")

        logger.info("Finished streaming data export to S3.")


def full_export(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    yield from export_organisation(organisation_id)
    yield from export_projects(organisation_id)
    yield from export_environments(organisation_id)
    yield from export_identities(organisation_id)
    yield from export_features(organisation_id)
    yield from export_metadata(organisation_id)
    yield from export_edge_identities(organisation_id)


def export_organisation(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    """
    Serialize an organisation and all its related objects.
    """
    yield from _export_entities(
        _EntityExportConfig(Organisation, Q(id=organisation_id)),
        _EntityExportConfig(InviteLink, Q(organisation__id=organisation_id)),
        _EntityExportConfig(OrganisationWebhook, Q(organisation__id=organisation_id)),
        _EntityExportConfig(Subscription, Q(organisation__id=organisation_id)),
    )


def export_metadata(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    yield from _export_entities(
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


def export_projects(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    default_filter = Q(project__organisation__id=organisation_id)

    for project in _export_entities(
        _EntityExportConfig(Project, Q(organisation__id=organisation_id)),
    ):
        project["fields"]["enable_dynamo_db"] = False
        yield project

    yield from _export_entities(
        _EntityExportConfig(
            Segment,
            Q(project__organisation__id=organisation_id, id=F("version_of")),
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


def export_environments(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    default_filter = Q(environment__project__organisation__id=organisation_id)

    yield from _export_entities(
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


def export_identities(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    # We export the traits first so that we take a 'snapshot' before exporting the
    # identities, otherwise we end up with issues where new traits are created for new
    # identities during the export process and the identity doesn't exist in the import.
    # We then need to reverse the order so that the identities are imported first.
    traits = list(
        _export_entities(
            _EntityExportConfig(
                Trait,
                Q(
                    identity__environment__project__organisation__id=organisation_id,
                    identity__environment__project__enable_dynamo_db=False,
                ),
            ),
        )
    )

    yield from _export_entities(
        _EntityExportConfig(
            Identity,
            Q(
                environment__project__organisation__id=organisation_id,
                environment__project__enable_dynamo_db=False,
            ),
        ),
    )

    yield from traits


def export_edge_identities(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    for environment in Environment.objects.filter(
        project__organisation__id=organisation_id, project__enable_dynamo_db=True
    ):
        exported_identities, exported_traits, exported_overrides = (
            export_edge_identity_and_overrides(environment.api_key)
        )
        yield from exported_identities
        yield from exported_traits
        yield from exported_overrides


def export_features(
    organisation_id: int,
) -> Iterator[dict[str, typing.Any]]:
    """
    Export all features and related entities, except ChangeRequests.
    """

    # Buffer feature states because we need to modify them (remove change_request FK)
    # and they need to be imported after Feature, EnvironmentFeatureVersion, etc.
    feature_states: list[dict[str, typing.Any]] = []
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

    yield from _export_entities(
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

    # Feature states need to be imported in correct order (after features)
    yield from feature_states

    yield from _export_entities(
        _EntityExportConfig(
            FeatureStateValue,
            Q(feature_state__feature__project__organisation__id=organisation_id),
        ),
        _EntityExportConfig(
            MultivariateFeatureStateValue,
            Q(feature_state__feature__project__organisation__id=organisation_id),
        ),
    )


@dataclass
class _EntityExportConfig:
    model_class: type(Model)  # type: ignore[valid-type]
    qs_filter: Q
    exclude_fields: typing.List[str] = None  # type: ignore[assignment]


def _export_entities(
    *export_configs: _EntityExportConfig,
) -> Iterator[dict[str, typing.Any]]:
    for config in export_configs:
        args = ("python", config.model_class.objects.filter(config.qs_filter))
        kwargs: dict[str, typing.Any] = {}
        if config.exclude_fields:
            kwargs["fields"] = [
                f.name
                for f in config.model_class._meta.get_fields()
                if f.name not in config.exclude_fields
            ]
        yield from _serialize_natural(*args, **kwargs)


_serialize_natural = functools.partial(
    serializers.serialize,
    use_natural_primary_keys=True,
    use_natural_foreign_keys=True,
)
