import json
import re
import typing
import uuid
from decimal import Decimal

import boto3
from core.constants import STRING
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from flag_engine.segments.constants import ALL_RULE, EQUAL
from moto import mock_s3
from mypy_boto3_dynamodb.service_resource import Table

from environments.identities.models import Identity
from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.workflows.core.models import ChangeRequest
from import_export.export import (
    S3OrganisationExporter,
    export_edge_identities,
    export_environments,
    export_features,
    export_metadata,
    export_organisation,
    export_projects,
)
from integrations.amplitude.models import AmplitudeConfiguration
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
from organisations.models import Organisation, OrganisationWebhook
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule


def test_export_organisation(db):
    # Given
    # an organisation
    organisation_name = "test org"
    organisation = Organisation.objects.create(name=organisation_name)

    # and an invite link
    InviteLink.objects.create(organisation=organisation)

    # and a webhook
    OrganisationWebhook.objects.create(
        organisation=organisation, url="https://test.webhooks.com/"
    )

    # When
    export = export_organisation(organisation.id)

    # Then
    assert export

    # TODO: test whether the export is importable


def test_export_project(organisation):
    # Given
    # a project
    project_name = "test project"
    project = Project.objects.create(organisation=organisation, name=project_name)

    # a segment
    segment = Segment.objects.create(project=project, name="test segment")
    segment_rule = SegmentRule.objects.create(segment=segment, type=ALL_RULE)
    Condition(rule=segment_rule, operator=EQUAL, property="foo", value="bar")

    # a tag
    Tag.objects.create(label="tag", project=project, color="#000000")

    # and one of each of the integrations
    DataDogConfiguration.objects.create(project=project, api_key="api-key")
    NewRelicConfiguration.objects.create(project=project, api_key="api-key")
    SlackConfiguration.objects.create(project=project, api_token="api-token")

    # When
    export = export_projects(organisation.id)

    # Then
    assert export

    # TODO: test whether the export is importable


def test_export_environments(project):
    # Given
    # an environment
    environment_name = "test environment"
    environment = Environment.objects.create(project=project, name=environment_name)

    # an environment API key
    EnvironmentAPIKey.objects.create(environment=environment)

    # a wehbook
    Webhook.objects.create(environment=environment, url="https://test.webhook.com")

    # and one of each of all the integrations...
    AmplitudeConfiguration.objects.create(environment=environment, api_key="api-key")
    HeapConfiguration.objects.create(environment=environment, api_key="api-key")
    MixpanelConfiguration.objects.create(environment=environment, api_key="api-key")
    SegmentConfiguration.objects.create(environment=environment, api_key="api-key")
    RudderstackConfiguration.objects.create(environment=environment, api_key="api-key")
    WebhookConfiguration.objects.create(
        environment=environment, url="https://test.webhook.com"
    )
    slack_project_config = SlackConfiguration.objects.create(
        project=project, api_token="api-token"
    )
    SlackEnvironment.objects.create(
        environment=environment,
        slack_configuration=slack_project_config,
        channel_id="channel-id",
    )

    # When
    export = export_environments(project.organisation_id)

    # Then
    assert export

    # TODO: test whether the export is importable


def test_export_metadata(environment, organisation, settings):
    # Given
    environment_type = ContentType.objects.get_for_model(environment)

    metadata_field = MetadataField.objects.create(
        name="test_field", type="int", organisation=organisation
    )

    environment_metadata_field = MetadataModelField.objects.create(
        field=metadata_field, content_type=environment_type
    )
    required_for_project = MetadataModelFieldRequirement.objects.create(
        model_field=environment_metadata_field, content_object=environment.project
    )

    environment_metadata = Metadata.objects.create(
        object_id=environment.id,
        content_type=environment_type,
        model_field=environment_metadata_field,
        field_value="some_data",
    )
    # When
    exported_environment = export_environments(environment.project.organisation_id)
    exported_metadata = export_metadata(organisation.id)

    data = exported_environment + exported_metadata

    # Now,to mimic a somewhat clean import, let's remove the metadata field
    # Which in turn will remove the metadata object
    metadata_field.delete()

    # and the environment(use hard_delete instead of (soft)delete to avoid api_key collision)
    environment.hard_delete()

    # Next, let's load the data
    file_path = f"/tmp/{uuid.uuid4()}.json"
    with open(file_path, "a+") as f:
        f.write(json.dumps(data, cls=DjangoJSONEncoder))
        f.seek(0)

        call_command("loaddata", f.name, format="json")

    # Finally
    # Metadata field exists
    assert MetadataField.objects.filter(uuid=metadata_field.uuid)

    # metadata model field requirements are correctly wired up
    metadata_model_field = MetadataModelField.objects.get(
        uuid=environment_metadata_field.uuid
    )
    requrired_for_project = MetadataModelFieldRequirement.objects.get(
        uuid=required_for_project.uuid
    )
    assert metadata_model_field == requrired_for_project.model_field
    assert requrired_for_project.content_type.model == "project"

    # and metadata correctly points to the loaded environment
    metadata = Metadata.objects.get(uuid=environment_metadata.uuid)
    loaded_environment = Environment.objects.get(api_key=environment.api_key)

    assert metadata.content_object == loaded_environment


def test_export_features(project, environment, segment, admin_user):
    # Given
    # a standard feature
    standard_feature = Feature.objects.create(project=project, name="standard_feature")
    standard_feature.owners.add(admin_user)

    # and a multivariate feature
    mv_feature = Feature.objects.create(
        project=project, name="mv_feature", type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type=STRING,
        string_value="foo",
    )

    # and a segment feature state
    feature_segment = FeatureSegment.objects.create(
        feature=standard_feature, segment=segment, environment=environment
    )
    FeatureState.objects.create(
        feature=standard_feature,
        feature_segment=feature_segment,
        environment=environment,
    )

    # and a feature state associated with a change request
    cr = ChangeRequest.objects.create(
        environment=environment, title="Test CR", user=admin_user
    )
    FeatureState.objects.create(
        feature=standard_feature, environment=environment, version=2, change_request=cr
    )

    # When
    export = export_features(organisation_id=project.organisation_id)

    # Then
    assert export

    json_export = json.dumps(export, cls=DjangoJSONEncoder)

    # verify that owners are not included in the export
    assert "owners" not in json_export

    # verify that change requests are not included in the export and that any feature
    # states associated with a change request are no longer associated with that CR.
    assert "workflows_core.changerequest" not in json_export
    assert not re.findall(r"\"change_request\": \[\"[a-z0-9\-]{36}\"\]", json_export)

    # TODO: test whether the export is importable


def test_export_features_with_environment_feature_version(
    project, environment, segment, admin_user
):
    # Given
    # an environment configured to use v2 feature versioning
    environment.use_v2_feature_versioning = True
    environment.save()

    # a standard feature
    Feature.objects.create(project=project, name="standard_feature")

    # When
    export = export_features(organisation_id=project.organisation_id)

    # Then
    assert export

    for item in export:
        if item["model"] == "versioning.EnvironmentFeatureVersion":
            assert item["fields"]["uuid"]
        elif item["model"] == "features.FeatureState":
            assert item["fields"]["environment_feature_version"]

    # TODO: test whether the export is importable


def test_export_edge_identities(
    flagsmith_identities_table: Table,
    project: Project,
    environment: Environment,
    multivariate_feature: Feature,
    multivariate_options: typing.List[MultivariateFeatureOption],
):
    # Given
    project.enable_dynamo_db = True
    project.save()

    # First, let's create some features(to override)
    int_feature = Feature.objects.create(
        project=project, name="int_feature", initial_value=11
    )
    float_feature = Feature.objects.create(
        project=project, name="float_feature", initial_value=11.1
    )
    bool_feature = Feature.objects.create(
        project=project, name="bool_feature", initial_value=True
    )

    # Let's create another feature that we are not going to override
    Feature.objects.create(project=project, name="string_feature", initial_value="foo")

    mv_option = multivariate_options[0]

    identity_identifier = "Development_user_123456"
    mv_override_fs_uuid = "b7c3d9e9-0bcc-4e60-8264-43e84b00fcbd"
    int_override_fs_uuid = "c6f9cec7-f27b-4e4f-80ff-5a2dfa3d4d20"
    float_override_fs_uuid = "b90eafdc-56f3-45ba-965f-e245007f3050"
    bool_override_fs_uuid = "2dab9fe3-49df-41ec-adc1-30f5dfe0b855"

    identity_document = {
        "composite_key": f"{environment.api_key}_{identity_identifier}",
        "created_date": "2024-09-22T07:27:27.770956+00:00",
        "django_id": None,
        "environment_api_key": environment.api_key,
        "identifier": identity_identifier,
        "identity_features": [
            {
                "django_id": None,
                "enabled": False,
                "feature": {
                    "id": multivariate_feature.id,
                    "name": multivariate_feature.name,
                    "type": "MULTIVARIATE",
                },
                "featurestate_uuid": mv_override_fs_uuid,
                "feature_segment": None,
                "feature_state_value": "control",
                "multivariate_feature_state_values": [
                    {
                        "id": None,
                        "multivariate_feature_option": {
                            "id": mv_option.id,
                            "value": mv_option.string_value,
                        },
                        "mv_fs_value_uuid": "1897c9df-b8fa-4870-a077-f48eadbf3aac",
                        "percentage_allocation": 100,
                    }
                ],
            },
            {
                "django_id": None,
                "enabled": True,
                "feature": {
                    "id": int_feature.id,
                    "name": int_feature.name,
                    "type": "STANDARD",
                },
                "featurestate_uuid": int_override_fs_uuid,
                "feature_segment": None,
                "feature_state_value": 123,
                "multivariate_feature_state_values": [],
            },
            {
                "django_id": None,
                "enabled": True,
                "feature": {
                    "id": float_feature.id,
                    "name": int_feature.name,
                    "type": "STANDARD",
                },
                "featurestate_uuid": float_override_fs_uuid,
                "feature_segment": None,
                "feature_state_value": Decimal("123.123"),
                "multivariate_feature_state_values": [],
            },
            {
                "django_id": None,
                "enabled": True,
                "feature": {
                    "id": bool_feature.id,
                    "name": int_feature.name,
                    "type": "STANDARD",
                },
                "featurestate_uuid": bool_override_fs_uuid,
                "feature_segment": None,
                "feature_state_value": False,
                "multivariate_feature_state_values": [],
            },
        ],
        "identity_traits": [
            {"trait_key": "int_trait", "trait_value": 123},
            {"trait_key": "float_trait", "trait_value": Decimal("123.123")},
            {"trait_key": "str_trait", "trait_value": "some-string"},
            {"trait_key": "bool_trait", "trait_value": True},
        ],
        "identity_uuid": "37ecaac3-70dd-4135-b2ee-9b2e3ffdc028",
    }
    flagsmith_identities_table.put_item(Item=identity_document)

    # When
    export_json = export_edge_identities(project.organisation_id)

    # Let's load the data
    file_path = f"/tmp/{uuid.uuid4()}.json"
    with open(file_path, "a+") as f:
        f.write(json.dumps(export_json, cls=DjangoJSONEncoder))
        f.seek(0)

        call_command("loaddata", f.name, format="json")
    # Then
    # the identity was created
    identity = Identity.objects.get(identifier=identity_identifier)

    # With the traits that were part of the document
    traits = identity.get_all_user_traits()
    all_feature_states = identity.get_all_feature_states()

    assert len(traits) == 4
    int_trait = traits[0]
    assert int_trait.trait_key == "int_trait"
    assert int_trait.trait_value == 123

    float_trait = traits[1]
    assert float_trait.trait_key == "float_trait"
    assert float_trait.trait_value == 123.123

    str_trait = traits[2]
    assert str_trait.trait_key == "str_trait"
    assert str_trait.trait_value == "some-string"

    bool_trait = traits[3]
    assert bool_trait.trait_key == "bool_trait"
    assert bool_trait.trait_value is True

    # And the feature states that were part of the document
    assert len(all_feature_states) == 5

    actual_mv_override = all_feature_states[0]
    assert str(actual_mv_override.uuid) == mv_override_fs_uuid
    assert (
        actual_mv_override.get_feature_state_value(identity=identity)
        == mv_option.string_value
    )

    actual_int_override = all_feature_states[1]
    assert str(actual_int_override.uuid) == int_override_fs_uuid
    assert actual_int_override.get_feature_state_value(identity=identity) == 123

    actual_float_override = all_feature_states[2]
    assert str(actual_float_override.uuid) == float_override_fs_uuid
    assert actual_float_override.get_feature_state_value(identity=identity) == "123.123"

    actual_bool_override = all_feature_states[3]
    assert str(actual_bool_override.uuid) == bool_override_fs_uuid
    assert actual_bool_override.get_feature_state_value(identity=identity) is False

    actual_string_fs = all_feature_states[4]
    assert actual_string_fs.get_feature_state_value(identity=identity) == "foo"
    assert actual_string_fs.identity is None


@mock_s3
def test_organisation_exporter_export_to_s3(organisation):
    # Given
    bucket_name = "test-bucket"
    file_key = "organisation-exports/org-1.json"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )

    s3_client = boto3.client("s3")

    exporter = S3OrganisationExporter(s3_client=s3_client)

    # When
    exporter.export_to_s3(organisation.id, bucket_name, file_key)

    # Then
    retrieved_object = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    assert retrieved_object.get("ContentLength", 0) > 0
