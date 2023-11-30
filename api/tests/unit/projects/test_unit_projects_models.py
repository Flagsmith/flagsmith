from datetime import timedelta
from unittest import mock

import pytest
from django.conf import settings
from django.utils import timezone

from audit.models import AuditLog, RelatedObjectType
from projects.models import (
    IdentityOverridesV2MigrationStatus,
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions import CREATE_FEATURE, MANAGE_SEGMENTS, VIEW_PROJECT

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
    "edge_release_datetime, expected_enable_dynamo_db_value",
    ((yesterday, True), (tomorrow, False), (None, False)),
)
def test_create_project_sets_enable_dynamo_db(
    db, edge_release_datetime, expected_enable_dynamo_db_value, settings, organisation
):
    # Given
    settings.EDGE_RELEASE_DATETIME = edge_release_datetime

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
    "identity_overrides_v2_migration_status, expected_value",
    (
        (IdentityOverridesV2MigrationStatus.NOT_STARTED, False),
        (IdentityOverridesV2MigrationStatus.IN_PROGRESS, False),
        (IdentityOverridesV2MigrationStatus.COMPLETE, True),
    ),
)
def test_show_edge_identity_overrides_for_feature(
    identity_overrides_v2_migration_status: IdentityOverridesV2MigrationStatus,
    expected_value: bool,
):
    assert (
        Project(
            identity_overrides_v2_migration_status=identity_overrides_v2_migration_status
        ).show_edge_identity_overrides_for_feature
        == expected_value
    )




@pytest.mark.django_db()
def test_create_update_delete_project_audit_log(mocker, organisation, admin_user):
    # Given
    mocker.patch("core.models._get_request_user", return_value=admin_user)

    # When
    project = Project.objects.create(name="Test project", organisation=organisation)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.PROJECT.name
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.PROJECT.name
    assert audit_log.related_object_id == project.pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"New Project created: {project.name}"

    # When
    project.name = new_name = "Test project changed"
    project.save()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.PROJECT.name
        ).count()
        == 2
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.PROJECT.name
    assert audit_log.related_object_id == project.pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"Project name updated: {new_name}"

    # When
    project.delete()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.PROJECT.name
        ).count()
        == 3
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.PROJECT.name
    assert audit_log.related_object_id == project.pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"Project deleted: {new_name}"


@pytest.mark.django_db()
def test_create_update_delete_user_project_permissions_audit_log(
    mocker, organisation, project, admin_user
):
    # Given
    mocker.patch("core.models._get_request_user", return_value=admin_user)

    # When
    perm = UserProjectPermission.objects.create(
        user=admin_user, project=project, admin=True
    )

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GRANT.name
    assert audit_log.related_object_id == perm.pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"New Grant created: {admin_user.email} / {project.name}"

    # When
    perm.add_permission(VIEW_PROJECT)
    perm.add_permission(CREATE_FEATURE)
    perm.admin = False
    perm.save()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 4
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GRANT.name
    assert audit_log.related_object_id == perm.pk
    assert audit_log.organisation_id == organisation.pk
    assert (
        audit_log.log == f"Grant admin set false: {admin_user.email} / {project.name}"
    )

    # When
    perm.set_permissions([VIEW_PROJECT, MANAGE_SEGMENTS])

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 6
    )
    audit_logs = AuditLog.objects.all()[0:2]
    assert audit_logs[0]
    assert audit_logs[0].author_id == admin_user.pk
    assert audit_logs[0].related_object_type == RelatedObjectType.GRANT.name
    assert audit_logs[0].related_object_id == perm.pk
    assert audit_logs[0].organisation_id == organisation.pk
    assert (
        audit_logs[0].log
        == f"Grant permissions updated: {admin_user.email} / {project.name}; added: {MANAGE_SEGMENTS}"
    )
    assert audit_logs[1]
    assert audit_logs[1].author_id == admin_user.pk
    assert audit_logs[1].related_object_type == RelatedObjectType.GRANT.name
    assert audit_logs[1].related_object_id == perm.pk
    assert audit_logs[1].organisation_id == organisation.pk
    assert (
        audit_logs[1].log
        == f"Grant permissions updated: {admin_user.email} / {project.name}; removed: {CREATE_FEATURE}"
    )

    # When
    perm_pk = perm.pk
    perm.delete()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 7
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GRANT.name
    assert audit_log.related_object_id == perm_pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"Grant deleted: {admin_user.email} / {project.name}"


@pytest.mark.django_db()
def test_create_update_delete_group_project_permissions_audit_log(
    mocker, organisation, project, admin_user, user_permission_group
):
    # Given
    mocker.patch("core.models._get_request_user", return_value=admin_user)

    # When
    perm = UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project, admin=True
    )

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GRANT.name
    assert audit_log.related_object_id == perm.pk
    assert audit_log.organisation_id == organisation.pk
    assert (
        audit_log.log
        == f"New Grant created: {user_permission_group.name} / {project.name}"
    )

    # When
    perm.add_permission(VIEW_PROJECT)
    perm.add_permission(CREATE_FEATURE)
    perm.admin = False
    perm.save()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 4
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GRANT.name
    assert audit_log.related_object_id == perm.pk
    assert audit_log.organisation_id == organisation.pk
    assert (
        audit_log.log
        == f"Grant admin set false: {user_permission_group.name} / {project.name}"
    )

    # When
    perm.set_permissions([VIEW_PROJECT, MANAGE_SEGMENTS])

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 6
    )
    audit_logs = AuditLog.objects.all()[0:2]
    assert audit_logs[0]
    assert audit_logs[0].author_id == admin_user.pk
    assert audit_logs[0].related_object_type == RelatedObjectType.GRANT.name
    assert audit_logs[0].related_object_id == perm.pk
    assert audit_logs[0].organisation_id == organisation.pk
    assert (
        audit_logs[0].log
        == f"Grant permissions updated: {user_permission_group.name} / {project.name}; added: {MANAGE_SEGMENTS}"
    )
    assert audit_logs[1]
    assert audit_logs[1].author_id == admin_user.pk
    assert audit_logs[1].related_object_type == RelatedObjectType.GRANT.name
    assert audit_logs[1].related_object_id == perm.pk
    assert audit_logs[1].organisation_id == organisation.pk
    assert (
        audit_logs[1].log
        == f"Grant permissions updated: {user_permission_group.name} / {project.name}; removed: {CREATE_FEATURE}"
    )

    # When
    perm_pk = perm.pk
    perm.delete()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GRANT.name
        ).count()
        == 7
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GRANT.name
    assert audit_log.related_object_id == perm_pk
    assert audit_log.organisation_id == organisation.pk
    assert (
        audit_log.log == f"Grant deleted: {user_permission_group.name} / {project.name}"
    )
