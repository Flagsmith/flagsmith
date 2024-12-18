from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.dynamodb.types import (
    IdentityOverridesV2List,
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


def get_edge_identity_overrides_for_feature_ids(
    environment_id: int,
    feature_ids: None | list[int] = None,
) -> list[IdentityOverridesV2List]:
    query_responses = (
        ddb_environment_v2_wrapper.get_identity_overrides_by_environment_id(
            environment_id=environment_id,
            feature_ids=feature_ids,
        )
    )

    results = []
    for identity_overrides_query_response in query_responses:
        identity_overrides = [
            IdentityOverrideV2.model_validate(
                {**item, "environment_id": str(item["environment_id"])}
            )
            for item in identity_overrides_query_response.items
        ]
        complete = identity_overrides_query_response.is_num_identity_overrides_complete
        results.append(
            IdentityOverridesV2List(
                identity_overrides=identity_overrides,
                is_num_identity_overrides_complete=complete,
            )
        )

    return results
