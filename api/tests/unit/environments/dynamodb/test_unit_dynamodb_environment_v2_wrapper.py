# import uuid

# from mypy_boto3_dynamodb.service_resource import Table
# from pytest_django.fixtures import SettingsWrapper

# from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper
# from environments.models import Environment
# from features.models import Feature

# def test_environment_v2_wrapper_get_identity_overrides(
#     settings: SettingsWrapper,
#     environment: Environment,
#     flagsmith_environments_v2_table: Table,
#     feature: Feature,
# ) -> None:
#     # Given
#     settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_v2_table.name
#     wrapper = DynamoEnvironmentV2Wrapper()

#     identity_uuid = str(uuid.uuid4())
#     identifier = "identity1"
#     override_document = {
#         "environment_id": environment.id,
#         "document_key": f"identity_override:{feature.id}:{identity_uuid}",
#         "environment_api_key": environment.api_key,
#         "identifier": identifier,
#         "feature_state": {},
#     }

#     environment_document = map_environment_to_environment_v2_document(environment)

#     flagsmith_environments_v2_table.put_item(Item=override_document)
#     flagsmith_environments_v2_table.put_item(Item=environment_document)

#     # When
#     results = wrapper.get_identity_overrides(environment_id=environment.id)

#     # Then
#     assert len(results) == 1
#     assert results[0] == override_document
