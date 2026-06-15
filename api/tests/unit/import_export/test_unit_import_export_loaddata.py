import json
import typing
import uuid

from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from flag_engine.segments.constants import ALL_RULE, EQUAL

from core.constants import STRING
from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.versioning.models import EnvironmentFeatureVersion
from import_export.export import full_export
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule


def _dump_and_load(data: typing.List[dict]) -> None:  # type: ignore[type-arg]
    file_path = f"/tmp/{uuid.uuid4()}.json"
    with open(file_path, "w") as f:
        f.write(json.dumps(data, cls=DjangoJSONEncoder))
    call_command("loaddata", file_path, format="json")


def test_full_export_loaddata__core_models__roundtrips_without_duplicates(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
    segment: Segment,
):
    # Given
    tag = Tag.objects.create(label="test-tag", project=project, color="#000000")
    feature.tags.add(tag)

    segment_rule = SegmentRule.objects.create(segment=segment, type=ALL_RULE)
    Condition.objects.create(
        rule=segment_rule, operator=EQUAL, property="plan", value="enterprise"
    )

    # Capture natural keys before export
    org_uuid = organisation.uuid
    project_uuid = project.uuid
    env_api_key = environment.api_key
    feature_uuid = feature.uuid
    segment_uuid = segment.uuid

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then - objects still exist with the same natural keys
    assert Organisation.objects.filter(uuid=org_uuid).exists()
    assert Project.objects.filter(uuid=project_uuid).exists()
    assert Environment.objects.filter(api_key=env_api_key).exists()
    assert Feature.objects.filter(uuid=feature_uuid).exists()
    assert Segment.objects.filter(uuid=segment_uuid).exists()
    assert Tag.objects.filter(uuid=tag.uuid).exists()

    # Verify no duplicates were created
    assert Organisation.objects.filter(uuid=org_uuid).count() == 1
    assert Project.objects.filter(uuid=project_uuid).count() == 1
    assert Environment.objects.filter(api_key=env_api_key).count() == 1
    assert Feature.objects.filter(uuid=feature_uuid).count() == 1


def test_full_export_loaddata__v2_versioning_enabled__roundtrips_correctly(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    # Given
    environment.use_v2_feature_versioning = True
    environment.save()

    feature = Feature.objects.create(project=project, name="v2_feature")

    efv = EnvironmentFeatureVersion.objects.filter(
        feature=feature, environment=environment
    ).first()
    assert efv is not None

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert EnvironmentFeatureVersion.objects.filter(uuid=efv.uuid).exists()
    loaded_efv = EnvironmentFeatureVersion.objects.get(uuid=efv.uuid)
    assert loaded_efv.feature == feature
    assert loaded_efv.environment == environment


def test_full_export_loaddata__feature_flag_value_updated__updates_on_reload(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    # Given - initial load
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Capture the initial feature state value
    fs = FeatureState.objects.get(
        feature=feature, environment=environment, identity=None, feature_segment=None
    )
    initial_fsv = fs.feature_state_value
    assert initial_fsv.string_value != "updated_value"

    # When - update the feature state value and re-export/load
    initial_fsv.string_value = "updated_value"
    initial_fsv.save()

    updated_data = full_export(organisation.id)
    _dump_and_load(updated_data)

    # Then - the feature state value is updated
    fs.refresh_from_db()
    fs.feature_state_value.refresh_from_db()
    assert fs.feature_state_value.string_value == "updated_value"


def test_full_export_loaddata__new_feature_added__creates_feature_on_reload(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    # Given
    data = full_export(organisation.id)
    _dump_and_load(data)

    initial_feature_count = Feature.objects.filter(
        project__organisation=organisation
    ).count()

    # When - create a new feature and re-export/load
    new_feature = Feature.objects.create(
        project=project, name="new_feature", initial_value="hello"
    )

    updated_data = full_export(organisation.id)
    _dump_and_load(updated_data)

    # Then - the new feature exists
    assert Feature.objects.filter(uuid=new_feature.uuid).exists()
    assert (
        Feature.objects.filter(project__organisation=organisation).count()
        == initial_feature_count + 1
    )

    # And its feature state value is correct
    new_fs = FeatureState.objects.get(
        feature=new_feature,
        environment=environment,
        identity=None,
        feature_segment=None,
    )
    assert new_fs.feature_state_value.string_value == "hello"


def test_full_export_loaddata__multivariate_feature__roundtrips_correctly(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    # Given
    mv_feature = Feature.objects.create(
        project=project, name="mv_feature", type=MULTIVARIATE
    )
    option_a = MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=30,
        type=STRING,
        string_value="option_a",
    )
    option_b = MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=70,
        type=STRING,
        string_value="option_b",
    )

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert MultivariateFeatureOption.objects.filter(uuid=option_a.uuid).exists()
    assert MultivariateFeatureOption.objects.filter(uuid=option_b.uuid).exists()

    loaded_option_a = MultivariateFeatureOption.objects.get(uuid=option_a.uuid)
    assert loaded_option_a.string_value == "option_a"
    assert loaded_option_a.default_percentage_allocation == 30

    loaded_option_b = MultivariateFeatureOption.objects.get(uuid=option_b.uuid)
    assert loaded_option_b.string_value == "option_b"
    assert loaded_option_b.default_percentage_allocation == 70

    # Verify multivariate feature state values exist
    mv_fs = FeatureState.objects.get(
        feature=mv_feature,
        environment=environment,
        identity=None,
        feature_segment=None,
    )
    mv_fs_values = MultivariateFeatureStateValue.objects.filter(feature_state=mv_fs)
    assert mv_fs_values.count() == 2


def test_full_export_loaddata__segments_with_rules_and_conditions__roundtrips_correctly(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
):
    # Given
    segment = Segment.objects.create(project=project, name="power_users")
    rule = SegmentRule.objects.create(segment=segment, type=ALL_RULE)
    Condition.objects.create(
        rule=rule, operator=EQUAL, property="subscription", value="premium"
    )

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert Segment.objects.filter(uuid=segment.uuid).exists()
    loaded_segment = Segment.objects.get(uuid=segment.uuid)
    assert loaded_segment.name == "power_users"

    loaded_rules = SegmentRule.objects.filter(segment=loaded_segment)
    assert loaded_rules.count() == 1

    loaded_conditions = Condition.objects.filter(rule=loaded_rules.first())
    assert loaded_conditions.count() == 1
    loaded_condition = loaded_conditions.first()
    assert loaded_condition is not None
    assert loaded_condition.property == "subscription"
    assert loaded_condition.value == "premium"


def test_full_export_loaddata__identity_overrides__roundtrips_correctly(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    # Given
    identity = Identity.objects.create(
        identifier="override_user", environment=environment
    )
    identity_fs = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity
    )
    identity_fs.enabled = True
    identity_fs.save()
    identity_fs.feature_state_value.string_value = "user_specific_value"
    identity_fs.feature_state_value.save()

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    loaded_fs = FeatureState.objects.get(uuid=identity_fs.uuid)
    assert loaded_fs.identity is not None
    assert loaded_fs.identity.identifier == "override_user"
    assert loaded_fs.enabled is True
    assert loaded_fs.feature_state_value.string_value == "user_specific_value"
