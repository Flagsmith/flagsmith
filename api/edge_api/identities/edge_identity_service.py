import typing
from collections import defaultdict
from typing import Any, Generator

from django.core.exceptions import ObjectDoesNotExist

from edge_api.identities.dataclasses import (
    OrphanedIdentityOverride,
    OrphanedIdentityOverrideReason,
)
from edge_api.identities.models import EdgeIdentity
from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.dynamodb.constants import DYNAMODB_MAX_BATCH_GET_ITEM_COUNT
from environments.dynamodb.types import (
    IdentityOverrideV2,
)
from util.engine_models.identities.models import IdentityModel
from util.util import iter_chunks

if typing.TYPE_CHECKING:
    from environments.models import Environment

ddb_environment_v2_wrapper = DynamoEnvironmentV2Wrapper()


def get_edge_identity_overrides(
    environment_id: int,
    feature_id: int | None = None,
) -> list[IdentityOverrideV2]:
    override_items = (
        ddb_environment_v2_wrapper.get_identity_overrides_by_environment_id(
            environment_id=environment_id,
            feature_id=feature_id,
        )
    )
    return [
        IdentityOverrideV2.model_validate(
            {**item, "environment_id": str(item["environment_id"])}
        )
        for item in override_items
    ]


def get_edge_identity_override_keys(environment_id: int) -> list[str]:
    """
    Get all the identity overrides for an environment, returning only the document key
    for optimised performance when the key is all that is needed.
    """
    override_items = (
        ddb_environment_v2_wrapper.get_identity_overrides_by_environment_id(
            environment_id=environment_id,
            projection_expression_attributes=["document_key"],
        )
    )
    return [item["document_key"] for item in override_items]


def iter_orphaned_identity_overrides(
    environment: "Environment",
) -> Generator[OrphanedIdentityOverride, None, None]:
    """
    Yield the environment's identity overrides that its identities no longer have.

    The identity document is the source of truth: it is what remote evaluation
    and the identity page read. An `environments_v2` override the identity does
    not have is therefore stale, and is still served to local evaluation SDKs
    and listed on the feature's identity overrides tab.
    """
    override_documents = (
        ddb_environment_v2_wrapper.get_identity_overrides_by_environment_id(
            environment_id=environment.id,
            projection_expression_attributes=[
                "document_key",
                "identifier",
                "identity_uuid",
                "feature_state.feature",
            ],
        )
    )
    documents_by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for override_document in override_documents:
        documents_by_identifier[override_document["identifier"]].append(
            override_document
        )

    for identifiers in iter_chunks(
        documents_by_identifier,
        chunk_size=DYNAMODB_MAX_BATCH_GET_ITEM_COUNT,
    ):
        identifiers_by_composite_key = {
            IdentityModel.generate_composite_key(
                environment.api_key, identifier
            ): identifier
            for identifier in identifiers
        }
        identity_documents = {
            identity_document["composite_key"]: identity_document
            for identity_document in EdgeIdentity.dynamo_wrapper.iter_items_by_composite_keys(
                identifiers_by_composite_key,
                projection_expression="composite_key,identity_uuid,identity_features",
            )
        }
        for composite_key, identifier in identifiers_by_composite_key.items():
            identity_document = identity_documents.get(composite_key)
            for override_document in documents_by_identifier[identifier]:
                feature = override_document["feature_state"]["feature"]
                if reason := _get_orphaned_identity_override_reason(
                    override_document=override_document,
                    identity_document=identity_document,
                ):
                    yield OrphanedIdentityOverride(
                        document_key=override_document["document_key"],
                        identifier=identifier,
                        identity_uuid=override_document["identity_uuid"],
                        feature_id=int(feature["id"]),
                        feature_name=feature["name"],
                        reason=reason,
                    )


def delete_orphaned_identity_override(
    environment_id: int,
    orphaned_identity_override: OrphanedIdentityOverride,
) -> bool:
    """
    Delete a stale identity override, unless it has been rewritten since it was read.

    :return: whether the override was deleted.
    """
    return ddb_environment_v2_wrapper.delete_identity_override_if_unchanged(
        environment_id=environment_id,
        document_key=orphaned_identity_override.document_key,
        identity_uuid=orphaned_identity_override.identity_uuid,
    )


def _get_orphaned_identity_override_reason(
    override_document: dict[str, Any],
    identity_document: dict[str, Any] | None,
) -> OrphanedIdentityOverrideReason | None:
    if identity_document is None:
        return OrphanedIdentityOverrideReason.IDENTITY_DELETED
    if identity_document["identity_uuid"] != override_document["identity_uuid"]:
        return OrphanedIdentityOverrideReason.IDENTITY_UUID_CHANGED
    overridden_feature_ids = {
        int(feature_state["feature"]["id"])
        for feature_state in identity_document.get("identity_features") or []
    }
    if int(override_document["feature_state"]["feature"]["id"]) not in (
        overridden_feature_ids
    ):
        return OrphanedIdentityOverrideReason.OVERRIDE_REMOVED
    return None


def get_overridden_feature_ids_for_edge_identity(identity_uuid: str) -> set[int]:
    try:
        identity_document = EdgeIdentity.dynamo_wrapper.get_item_from_uuid(
            identity_uuid
        )
    except ObjectDoesNotExist:
        return set()
    identity = EdgeIdentity.from_identity_document(identity_document)
    return {fs.feature.id for fs in identity.feature_overrides}
