import typing

from flag_engine.features.models import FeatureStateModel

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper

ddb_environment_v2_wrapper = DynamoEnvironmentV2Wrapper()


class EdgeIdentityFeatureStateOverrideModel(FeatureStateModel):
    identity_uuid: str
    identifier: str


def get_edge_identity_overrides(
    environment_id: int, feature_id: int = None
) -> typing.List[EdgeIdentityFeatureStateOverrideModel]:
    override_items = ddb_environment_v2_wrapper.get_identity_overrides(
        environment_id, feature_id
    )
    return [
        EdgeIdentityFeatureStateOverrideModel.parse_obj(
            {
                **item["feature_state"],
                "identity_uuid": item["document_key"].rsplit(":")[-1],
                "identifier": item["identifier"],
            }
        )
        for item in override_items
    ]
