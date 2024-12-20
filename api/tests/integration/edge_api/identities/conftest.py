from typing import Any

import pytest
from boto3.dynamodb.conditions import Key
from flag_engine.identities.models import IdentityModel

from edge_api.identities.models import EdgeIdentity
from environments.dynamodb.wrappers.environment_wrapper import (
    DynamoEnvironmentV2Wrapper,
)
from users.models import FFAdminUser


@pytest.fixture()
def webhook_mock(mocker):
    return mocker.patch(
        "edge_api.identities.serializers.call_environment_webhook_for_feature_state_change"
    )


@pytest.fixture()
def identity_overrides_v2(
    dynamo_enabled_environment: int,
    identity_document_without_fs: dict[str, Any],
    identity_document: dict[str, Any],
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    admin_user: FFAdminUser,
) -> list[str]:
    edge_identity = EdgeIdentity.from_identity_document(identity_document_without_fs)
    for feature_override in IdentityModel.model_validate(
        identity_document
    ).identity_features:
        edge_identity.add_feature_override(feature_override)
    edge_identity.save(admin_user)
    return [
        item["document_key"]
        for item in dynamodb_wrapper_v2.query_iter_all_items(
            KeyConditionExpression=Key("environment_id").eq(
                str(dynamo_enabled_environment)
            ),
        )
    ]
