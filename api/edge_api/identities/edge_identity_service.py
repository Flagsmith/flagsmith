import typing

from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.dynamodb.types import IdentityOverrideV2

ddb_environment_v2_wrapper = DynamoEnvironmentV2Wrapper()


def get_edge_identity_overrides(
    environment_id: int,
    feature_id: int | None = None,
    feature_ids: None | list[int] = None,
    limit_feature_identities_to_one_page: bool = False,
) -> typing.List[IdentityOverrideV2]:
    override_items = (
        ddb_environment_v2_wrapper.get_identity_overrides_by_environment_id(
            environment_id=environment_id,
            feature_id=feature_id,
            feature_ids=feature_ids,
            limit_feature_identities_to_one_page=limit_feature_identities_to_one_page,
        )
    )
    return [
        IdentityOverrideV2.model_validate(
            {**item, "environment_id": str(item["environment_id"])}
        )
        for item in override_items
    ]
