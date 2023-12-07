import typing

from flag_engine.features.models import FeatureStateModel

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper

ddb_environment_v2_wrapper = DynamoEnvironmentV2Wrapper()


def get_edge_identity_overrides(
    environment_id: int, feature_id: int = None
) -> typing.List[FeatureStateModel]:
    # TODO: work out how to return the identity_uuid and identifier here too!
    data = ddb_environment_v2_wrapper.get_identity_overrides(environment_id, feature_id)
    return [FeatureStateModel.parse_obj(item["feature_state"]) for item in data]
