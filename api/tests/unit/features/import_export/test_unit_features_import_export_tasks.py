import json
from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE, STANDARD
from features.import_export.constants import (
    FAILED,
    OVERWRITE_DESTRUCTIVE,
    PROCESSING,
    SKIP,
    SUCCESS,
)
from features.import_export.models import (
    FeatureExport,
    FeatureImport,
    FlagsmithOnFlagsmithFeatureExport,
)
from features.import_export.tasks import (
    _create_flagsmith_on_flagsmith_feature_export,
    clear_stale_feature_imports_and_exports,
    export_features_for_environment,
    import_features_for_environment,
    retire_stalled_feature_imports_and_exports,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag


def test_clear_stale_feature_imports_and_exports(
    db: None, environment: Environment, freezer: FrozenDateTimeFactory
):
    # Given
    now = timezone.now()
    freezer.move_to(now - timedelta(days=28))
    lost_feature_export = FeatureExport.objects.create(
        data="{}",
        environment=environment,
    )
    lost_feature_import = FeatureImport.objects.create(
        data="{}",
        environment=environment,
    )

    freezer.move_to(now)
    kept_feature_export = FeatureExport.objects.create(
        data="{}",
        environment=environment,
    )
    kept_feature_import = FeatureImport.objects.create(
        data="{}",
        environment=environment,
    )

    # When
    clear_stale_feature_imports_and_exports()

    # Then
    with pytest.raises(FeatureImport.DoesNotExist):
        lost_feature_import.refresh_from_db()
    with pytest.raises(FeatureExport.DoesNotExist):
        lost_feature_export.refresh_from_db()

    kept_feature_import.refresh_from_db()
    kept_feature_export.refresh_from_db()


def test_retire_stalled_feature_imports_and_exports(
    db: None, environment: Environment, freezer: FrozenDateTimeFactory
):
    # Given
    now = timezone.now()
    freezer.move_to(now - timedelta(minutes=12))
    to_fail_feature_export = FeatureExport.objects.create(
        data="{}",
        environment=environment,
        status=PROCESSING,
    )
    to_fail_feature_import = FeatureImport.objects.create(
        data="{}",
        environment=environment,
        status=PROCESSING,
    )

    freezer.move_to(now)
    keep_processing_feature_export = FeatureExport.objects.create(
        data="{}",
        environment=environment,
        status=PROCESSING,
    )
    keep_processing_feature_import = FeatureImport.objects.create(
        data="{}",
        environment=environment,
        status=PROCESSING,
    )

    # When
    retire_stalled_feature_imports_and_exports()

    # Then
    to_fail_feature_import.refresh_from_db()
    to_fail_feature_export.refresh_from_db()
    keep_processing_feature_import.refresh_from_db()
    keep_processing_feature_export.refresh_from_db()

    assert to_fail_feature_import.status == FAILED
    assert to_fail_feature_export.status == FAILED
    assert keep_processing_feature_import.status == PROCESSING
    assert keep_processing_feature_export.status == PROCESSING


def test_export_and_import_features_for_environment_with_skip(
    db: None,
    environment: Environment,
    project: Project,
    identity: Identity,
    feature: Feature,
    feature_segment: FeatureSegment,
) -> None:
    # Given

    # Features included in the export.
    Feature.objects.create(
        name="1",
        project=project,
        initial_value="200",
        is_server_key_only=True,
        default_enabled=True,
    )
    Feature.objects.create(
        name="2",
        project=project,
        initial_value="banana",
        default_enabled=False,
    )
    Feature.objects.create(
        name="3",
        project=project,
        initial_value="changeme",
    )

    # Create the receiving organisation, project, etc.
    organisation2 = Organisation.objects.create(name="Receiving")
    project2 = Project.objects.create(name="Web", organisation=organisation2)
    environment2 = Environment.objects.create(name="Bat", project=project2)

    overlapping_feature = Feature.objects.create(
        name="3",
        project=project2,
        initial_value="keepme",
    )

    feature_export = FeatureExport.objects.create(
        environment=environment,
        status=PROCESSING,
    )

    # When
    export_features_for_environment(feature_export.id)

    feature_export.refresh_from_db()
    assert len(feature_export.data) > 200

    feature_import = FeatureImport.objects.create(
        environment=environment2,
        strategy=SKIP,
        data=feature_export.data,
    )
    import_features_for_environment(feature_import.id)

    # Then
    feature_import.refresh_from_db()
    assert feature_import.status == SUCCESS

    assert project2.features.count() == 4
    overlapping_feature.refresh_from_db()
    assert overlapping_feature.deleted_at is None
    assert project2.features.get(name="3") == overlapping_feature
    assert overlapping_feature.initial_value == "keepme"

    new_feature1 = project2.features.get(name="1")
    new_feature2 = project2.features.get(name="2")

    assert new_feature1.type == STANDARD
    assert new_feature1.initial_value == "200"
    assert new_feature1.is_server_key_only is True
    assert new_feature1.default_enabled is True

    assert new_feature2.type == STANDARD
    assert new_feature2.initial_value == "banana"
    assert new_feature2.is_server_key_only is False
    assert new_feature2.default_enabled is False


def test_export_and_import_features_for_environment_with_overwrite_destructive(
    db: None,
    environment: Environment,
    project: Project,
    identity: Identity,
    feature: Feature,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    # This environment should be ignored.
    Environment.objects.create(name="Dig", project=project)

    design_tag = Tag.objects.create(label="design", project=project, color="#228B22")
    sales_tag = Tag.objects.create(label="sales", project=project, color="#000080")
    feature1 = Feature.objects.create(
        name="1",
        project=project,
        initial_value="200",
        is_server_key_only=True,
        default_enabled=True,
    )
    feature2 = Feature.objects.create(
        name="2",
        project=project,
        initial_value="banana",
        default_enabled=False,
    )
    feature3 = Feature.objects.create(
        name="3",
        project=project,
        initial_value="changeme",
    )

    multivariate_feature_option1 = MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=30,
        type=STRING,
        string_value="mv_feature_option1",
    )
    multivariate_feature_option2 = MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=70,
        type=STRING,
        string_value="mv_feature_option2",
    )
    feature_state2 = feature2.feature_states.get(environment=environment)

    mv_feature_state_value1 = feature_state2.multivariate_feature_state_values.get(
        multivariate_feature_option=multivariate_feature_option1
    )
    mv_feature_state_value2 = feature_state2.multivariate_feature_state_values.get(
        multivariate_feature_option=multivariate_feature_option2
    )
    mv_feature_state_value1.percentage_allocation = 90
    mv_feature_state_value1.save()
    mv_feature_state_value2.percentage_allocation = 10
    mv_feature_state_value2.save()

    feature_state3 = feature3.feature_states.get(environment=environment)
    feature_state3.enabled = True
    feature_state3.save()

    feature_state3.feature_state_value.type = STRING
    feature_state3.feature_state_value.string_value = "changed"
    feature_state3.feature_state_value.save()

    # Not included in export because will not have design tag.
    Feature.objects.create(name="4", project=project)

    feature1.tags.add(design_tag, sales_tag)
    feature2.tags.add(design_tag)
    feature3.tags.add(design_tag)

    # These should be ignored
    FeatureState.objects.create(
        identity=identity, feature=feature1, environment=environment
    )
    FeatureState.objects.create(
        feature_segment=feature_segment, feature=feature2, environment=environment
    )

    # Create the receiving organisation, project, etc.
    organisation2 = Organisation.objects.create(name="Receiving")
    project2 = Project.objects.create(name="Web", organisation=organisation2)
    environment2 = Environment.objects.create(name="Bat", project=project2)
    Environment.objects.create(name="Ignore Me", project=project2)

    overlapping_feature = Feature.objects.create(
        name="3",
        project=project2,
        initial_value="keepme",
    )
    feature_export = FeatureExport.objects.create(
        environment=environment,
        status=PROCESSING,
    )

    # When
    export_features_for_environment(feature_export.id, [design_tag.id])

    feature_export.refresh_from_db()
    assert len(feature_export.data) > 200

    feature_import = FeatureImport.objects.create(
        environment=environment2,
        strategy=OVERWRITE_DESTRUCTIVE,
        data=feature_export.data,
    )
    import_features_for_environment(feature_import.id)

    # Then
    assert project2.features.count() == 3
    overlapping_feature.refresh_from_db()
    assert overlapping_feature.deleted_at < timezone.now()

    new_feature1 = project2.features.get(name="1")
    new_feature2 = project2.features.get(name="2")
    new_feature3 = project2.features.get(name="3")

    assert new_feature1.type == STANDARD
    assert new_feature1.initial_value == "200"
    assert new_feature1.is_server_key_only is True
    assert new_feature1.default_enabled is True

    assert new_feature2.type == MULTIVARIATE
    assert new_feature2.initial_value == "banana"
    assert new_feature2.is_server_key_only is False
    assert new_feature2.default_enabled is False

    queryset = new_feature2.feature_states.filter(
        environment=environment2,
    )
    assert queryset.count() == 1

    new_feature_state2 = queryset.first()

    assert new_feature2.multivariate_options.count() == 2
    new_mv_feature_option1 = new_feature2.multivariate_options.get(
        string_value="mv_feature_option1"
    )
    new_mv_feature_option2 = new_feature2.multivariate_options.get(
        string_value="mv_feature_option2"
    )

    new_mv_fs_value1 = new_feature_state2.multivariate_feature_state_values.get(
        multivariate_feature_option=new_mv_feature_option1
    )
    new_mv_fs_value2 = new_feature_state2.multivariate_feature_state_values.get(
        multivariate_feature_option=new_mv_feature_option2
    )
    assert new_mv_fs_value1.percentage_allocation == 90
    assert new_mv_fs_value2.percentage_allocation == 10

    assert new_mv_feature_option1.type == STRING
    assert new_mv_feature_option1.default_percentage_allocation == 30
    assert new_mv_feature_option2.type == STRING
    assert new_mv_feature_option2.default_percentage_allocation == 70

    assert new_feature3.type == STANDARD
    assert new_feature3.initial_value == "changeme"

    queryset = new_feature3.feature_states.filter(
        environment=environment2,
    )
    assert queryset.count() == 1

    new_feature_state3 = queryset.first()
    assert new_feature_state3.enabled is True
    assert new_feature_state3.feature_state_value.type == STRING
    assert new_feature_state3.feature_state_value.value == "changed"


def test_create_flagsmith_on_flagsmith_feature_export(
    db: None,
    settings: SettingsWrapper,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    flagsmith_tag = Tag.objects.create(
        label="flagsmith-on-flagsmith", project=project, color="#228B22"
    )
    feature = Feature.objects.create(
        name="fof_feature",
        project=project,
        initial_value="200",
        is_server_key_only=True,
        default_enabled=False,
    )
    feature.tags.add(flagsmith_tag)
    feature_state = feature.feature_states.get(environment=environment)
    feature_state.enabled = True
    feature_state.save()

    settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_ENVIRONMENT_ID = environment.id
    settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_TAG_ID = flagsmith_tag.id
    assert FlagsmithOnFlagsmithFeatureExport.objects.count() == 0

    # When
    _create_flagsmith_on_flagsmith_feature_export()

    # Then
    assert FlagsmithOnFlagsmithFeatureExport.objects.count() == 1
    fof = FlagsmithOnFlagsmithFeatureExport.objects.first()
    assert fof.feature_export.status == SUCCESS

    data = json.loads(fof.feature_export.data)
    assert len(data) == 1
    assert data[0]["name"] == "fof_feature"
    assert data[0]["default_enabled"] is False
    assert data[0]["enabled"] is True
