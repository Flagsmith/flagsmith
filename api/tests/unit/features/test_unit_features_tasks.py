from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from environments.identities.models import Identity
from environments.models import Environment
from features.constants import OVERWRITE, SKIP
from features.feature_types import MULTIVARIATE, STANDARD
from features.models import (
    Feature,
    FeatureExport,
    FeatureImport,
    FeatureSegment,
    FeatureState,
)
from features.multivariate.models import MultivariateFeatureOption
from features.tasks import (
    clear_stale_feature_imports_and_exports,
    export_features_for_environment,
    import_features_for_environment,
    trigger_feature_state_change_webhooks,
)
from features.value_types import STRING
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from webhooks.webhooks import WebhookEventType


def test_clear_stale_feature_imports_and_exports(db: None, environment: Environment):
    # Given
    four_weeks_ago = timezone.now() - timedelta(days=28)
    kept_feature_export = FeatureExport.objects.create(
        data="{}",
        environment=environment,
    )
    lost_feature_export = FeatureExport.objects.create(
        data="{}",
        environment=environment,
    )
    lost_feature_export.created_date = four_weeks_ago
    lost_feature_export.save()

    kept_feature_import = FeatureImport.objects.create(
        data="{}",
        environment=environment,
    )
    lost_feature_import = FeatureImport.objects.create(
        data="{}",
        environment=environment,
    )
    lost_feature_import.created_date = four_weeks_ago
    lost_feature_import.save()

    # When
    clear_stale_feature_imports_and_exports()

    # Then
    with pytest.raises(FeatureImport.DoesNotExist):
        lost_feature_import.refresh_from_db()
    with pytest.raises(FeatureExport.DoesNotExist):
        lost_feature_export.refresh_from_db()

    kept_feature_import.refresh_from_db()
    kept_feature_export.refresh_from_db()


def test_export_and_import_features_for_environment_with_skip(
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

    # When
    export_features_for_environment(environment.id)

    feature_export = FeatureExport.objects.get(
        environment=environment,
    )
    assert len(feature_export.data) > 200

    feature_import = FeatureImport.objects.create(
        environment=environment2,
        strategy=SKIP,
        data=feature_export.data,
    )
    import_features_for_environment(feature_import.id)

    # Then
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


def test_export_and_import_features_for_environment(
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

    # When
    export_features_for_environment(environment.id, [design_tag.id])

    feature_export = FeatureExport.objects.get(
        environment=environment,
    )
    assert len(feature_export.data) > 200

    feature_import = FeatureImport.objects.create(
        environment=environment2,
        strategy=OVERWRITE,
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


@pytest.mark.django_db
@mock.patch("features.tasks.Thread")
def test_trigger_feature_state_change_webhooks(MockThread):
    # Given
    initial_value = "initial"
    new_value = "new"

    organisation = Organisation.objects.create(name="Test organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    environment = Environment.objects.create(name="Test environment", project=project)
    feature = Feature.objects.create(
        name="Test feature", project=project, initial_value=initial_value
    )
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    MockThread.reset_mock()  # reset mock as it will have been called when setting up the data

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    call_list = MockThread.call_args_list

    environment_webhook_call_args = call_list[0]
    organisation_webhook_call_args = call_list[1]

    # verify that the data for both calls is the same
    assert (
        environment_webhook_call_args[1]["args"][1]
        == organisation_webhook_call_args[1]["args"][1]
    )

    data = environment_webhook_call_args[1]["args"][1]
    event_type = environment_webhook_call_args[1]["args"][2]
    assert data["new_state"]["feature_state_value"] == new_value
    assert data["previous_state"]["feature_state_value"] == initial_value
    assert event_type == WebhookEventType.FLAG_UPDATED


@pytest.mark.django_db
@mock.patch("features.tasks.Thread")
def test_trigger_feature_state_change_webhooks_for_deleted_flag(
    MockThread, organisation, project, environment, feature
):
    # Given
    new_value = "new"
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    MockThread.reset_mock()  # reset mock as it will have been called when setting up the data
    trigger_feature_state_change_webhooks(feature_state, WebhookEventType.FLAG_DELETED)

    # Then
    call_list = MockThread.call_args_list

    environment_webhook_call_args = call_list[0]
    organisation_webhook_call_args = call_list[1]

    # verify that the data for both calls is the same
    assert (
        environment_webhook_call_args[1]["args"][1]
        == organisation_webhook_call_args[1]["args"][1]
    )

    data = environment_webhook_call_args[1]["args"][1]
    event_type = environment_webhook_call_args[1]["args"][2]
    assert data["new_state"] is None
    assert data["previous_state"]["feature_state_value"] == new_value
    assert event_type == WebhookEventType.FLAG_DELETED
