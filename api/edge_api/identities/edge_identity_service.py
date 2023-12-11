import typing

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper
from environments.dynamodb.types import IdentityOverrideV2

ddb_environment_v2_wrapper = DynamoEnvironmentV2Wrapper()


def get_edge_identity_overrides(
    environment_id: int, feature_id: int
) -> typing.List[IdentityOverrideV2]:
    override_items = ddb_environment_v2_wrapper.get_identity_overrides_by_feature_id(
        environment_id=environment_id, feature_id=feature_id
    )
    return [IdentityOverrideV2.parse_obj(item) for item in override_items]
