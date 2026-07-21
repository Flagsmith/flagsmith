from django.core.exceptions import ObjectDoesNotExist

from edge_api.identities.models import EdgeIdentity
from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.dynamodb.types import (
    IdentityOverrideV2,
)

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


def get_overridden_feature_ids_for_edge_identity(identity_uuid: str) -> set[int]:
    try:
        identity_document = EdgeIdentity.dynamo_wrapper.get_item_from_uuid(
            identity_uuid
        )
    except ObjectDoesNotExist:
        return set()
    identity = EdgeIdentity.from_identity_document(identity_document)
    return {fs.feature.id for fs in identity.feature_overrides}
