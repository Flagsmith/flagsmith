from datetime import timedelta
from unittest import mock

import pytest
from django.conf import settings
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper

from organisations.models import Organisation
from projects.models import EdgeV2MigrationStatus, Project

now = timezone.now()
tomorrow = now + timedelta(days=1)
yesterday = now - timedelta(days=1)


@pytest.mark.django_db()
def test_get_segments_from_cache(project, monkeypatch):
    # Given
    mock_project_segments_cache = mock.MagicMock()
    mock_project_segments_cache.get.return_value = None

    monkeypatch.setattr(
        "projects.models.project_segments_cache", mock_project_segments_cache
    )

    # When
    segments = project.get_segments_from_cache()

    # Then
    mock_project_segments_cache.get.assert_called_with(project.id)
    mock_project_segments_cache.set.assert_called_with(
        project.id, segments, timeout=settings.CACHE_PROJECT_SEGMENTS_SECONDS
    )


@pytest.mark.django_db()
def test_get_segments_from_cache_set_not_called(project, segments, monkeypatch):
    # Given
    mock_project_segments_cache = mock.MagicMock()
    mock_project_segments_cache.get.return_value = project.segments.all()

    monkeypatch.setattr(
        "projects.models.project_segments_cache", mock_project_segments_cache
    )

    # When
    segments = project.get_segments_from_cache()

    # Then
    assert segments

    # And correct calls to cache are made
    mock_project_segments_cache.get.assert_called_once_with(project.id)
    mock_project_segments_cache.set.assert_not_called()


@pytest.mark.parametrize(
    "edge_enabled, expected_enable_dynamo_db_value",
    ((True, True), (False, False)),
)
def test_create_project_sets_enable_dynamo_db(
    db, edge_enabled, expected_enable_dynamo_db_value, settings, organisation
):
    # Given
    settings.EDGE_ENABLED = edge_enabled

    # When
    project = Project.objects.create(name="Test project", organisation=organisation)

    # Then
    assert project.enable_dynamo_db == expected_enable_dynamo_db_value


@pytest.mark.parametrize(
    "edge_release_datetime, expected",
    ((yesterday, True), (tomorrow, False), (None, False)),
)
def test_is_edge_project_by_default(
    settings, organisation, edge_release_datetime, expected
):
    # Given
    settings.EDGE_RELEASE_DATETIME = edge_release_datetime

    # When
    project = Project.objects.create(name="Test project", organisation=organisation)

    # Then
    assert project.is_edge_project_by_default == expected


@pytest.mark.parametrize(
    "feature_name_regex, feature_name, expected_result",
    (
        ("[a-z]+", "validfeature", True),
        ("[a-z]+", "InvalidFeature", False),
        ("^[a-z]+$", "validfeature", True),
        ("^[a-z]+$", "InvalidFeature", False),
    ),
)
def test_is_feature_name_valid(feature_name_regex, feature_name, expected_result):
    assert (
        Project(
            name="test", feature_name_regex=feature_name_regex
        ).is_feature_name_valid(feature_name)
        == expected_result
    )


def test_updating_project_clears_environment_caches(environment, project, mocker):
    # Given
    mock_environment_cache = mocker.patch("projects.models.environment_cache")

    # When
    project.name += "update"
    project.save()

    # Then
    mock_environment_cache.delete_many.assert_called_once_with([environment.api_key])


def test_environments_are_updated_in_dynamodb_when_project_id_updated(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mocker,
):
    # Given
    mock_environments_wrapper = mocker.patch("environments.models.environment_wrapper")

    # When
    dynamo_enabled_project.name = dynamo_enabled_project.name + " updated"
    dynamo_enabled_project.save()

    # Then
    mock_environments_wrapper.write_environments.assert_called_once_with(
        [dynamo_enabled_project_environment_one, dynamo_enabled_project_environment_two]
    )


@pytest.mark.parametrize(
    "edge_v2_migration_status, expected_value",
    (
        (EdgeV2MigrationStatus.NOT_STARTED, False),
        (EdgeV2MigrationStatus.IN_PROGRESS, False),
        (EdgeV2MigrationStatus.COMPLETE, True),
        (EdgeV2MigrationStatus.INCOMPLETE, False),
    ),
)
def test_show_edge_identity_overrides_for_feature(
    edge_v2_migration_status: EdgeV2MigrationStatus,
    expected_value: bool,
):
    assert (
        Project(
            edge_v2_migration_status=edge_v2_migration_status
        ).show_edge_identity_overrides_for_feature
        == expected_value
    )


def test_create_project_sets_edge_v2_migration_status_if_edge_enabled(
    settings: SettingsWrapper, organisation: Organisation
) -> None:
    # Given
    settings.EDGE_ENABLED = True

    # When
    project = Project.objects.create(name="test", organisation=organisation)

    # Then
    assert project.edge_v2_migration_status == EdgeV2MigrationStatus.COMPLETE
