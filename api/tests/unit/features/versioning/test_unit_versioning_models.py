import typing

import pytest
from django.utils import timezone
from freezegun import freeze_time

from environments.models import Environment
from environments.tasks import rebuild_environment_document
from features.models import FeatureSegment, FeatureState
from features.versioning.exceptions import FeatureVersioningError
from features.versioning.models import EnvironmentFeatureVersion
from segments.models import Segment

if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from features.models import Feature
    from projects.models import Project
    from users.models import FFAdminUser

now = timezone.now()


def test_create_new_environment_feature_version_clones_feature_states_from_previous_version(
    environment_v2_versioning, feature
):
    # Given
    original_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    segment = Segment.objects.create(project=environment_v2_versioning.project)
    feature_segment = FeatureSegment.objects.create(
        segment=segment, feature=feature, environment=environment_v2_versioning
    )
    FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment,
        environment_feature_version=original_version,
    )

    # When
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # Then
    # the version is given a uuid
    assert new_version.uuid

    # and the correct feature states are cloned and added to the new version
    assert new_version.feature_states.count() == 2
    assert new_version.feature_states.filter(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=None,
        identity=None,
    ).exists()
    assert new_version.feature_states.filter(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment__segment=segment,
        identity=None,
    ).exists()

    # but the existing feature states are left untouched
    assert (
        FeatureState.objects.filter(
            environment_feature_version=original_version
        ).count()
        == 2
    )


def test_environment_feature_version_create_initial_version_fails_for_v1_versioning_environment(
    feature: "Feature", project: "Project"
) -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=False
    )

    # When
    with pytest.raises(FeatureVersioningError) as e:
        EnvironmentFeatureVersion.create_initial_version(
            environment=environment, feature=feature
        )

    # Then
    assert (
        "Cannot create initial version for environment using v1 versioning"
        in e.exconly()
    )


def test_environment_feature_version_create_initial_version_fails_if_version_already_exists(
    feature: "Feature", project: "Project"
) -> None:
    # Given
    # Initial version is created as part of the hooks on the environment model
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    )

    # When
    with pytest.raises(FeatureVersioningError) as e:
        EnvironmentFeatureVersion.create_initial_version(
            environment=environment, feature=feature
        )

    # Then
    assert (
        "Version already exists for this feature / environment combination."
        in e.exconly()
    )


def test_get_previous_version(feature: "Feature", project: "Project") -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )

    version_1 = EnvironmentFeatureVersion.objects.get(
        environment=environment, feature=feature
    )
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    # Then
    assert version_2.get_previous_version() == version_1


def test_get_previous_version_ignores_unpublished_version(
    feature: "Feature", project: "Project"
) -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )

    version_1 = EnvironmentFeatureVersion.objects.get(
        environment=environment, feature=feature
    )
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )
    version_3 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    # Then
    assert version_2.is_live is False
    assert version_3.get_previous_version() == version_1


def test_publish(
    feature: "Feature",
    project: "Project",
    admin_user: "FFAdminUser",
    mocker: "MockerFixture",
) -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    mocked_rebuild_environment_document = mocker.patch(
        "features.versioning.receivers.rebuild_environment_document",
        autospec=rebuild_environment_document,
    )

    # When
    with freeze_time(now):
        version_2.publish(published_by=admin_user)

    # Then
    assert version_2.is_live
    assert version_2.live_from == now
    assert version_2.published is True
    assert version_2.published_by == admin_user

    mocked_rebuild_environment_document.delay.assert_called_once_with(
        kwargs={"environment_id": environment.id},
        delay_until=version_2.live_from,
    )


def test_update_version_webhooks_triggered_when_version_published(
    environment_v2_versioning: Environment,
    feature: "Feature",
    admin_user: "FFAdminUser",
    mocker: "MockerFixture",
) -> None:
    # Given
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
    )

    mock_trigger_update_version_webhooks = mocker.patch(
        "features.versioning.receivers.trigger_update_version_webhooks"
    )

    # When
    new_version.publish(admin_user)

    # Then
    mock_trigger_update_version_webhooks.delay.assert_called_once_with(
        kwargs={"environment_feature_version_uuid": str(new_version.uuid)},
        delay_until=new_version.live_from,
    )
