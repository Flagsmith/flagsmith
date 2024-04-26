import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from environments.dynamodb.types import ProjectIdentityMigrationStatus
from environments.identities.models import Identity
from features.models import Feature, FeatureSegment
from organisations.models import Organisation, Subscription
from organisations.permissions.models import (
    OrganisationPermissionModel,
    UserOrganisationPermission,
)
from organisations.permissions.permissions import CREATE_PROJECT
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions import (
    CREATE_ENVIRONMENT,
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from segments.models import Segment
from task_processor.task_run_method import TaskRunMethod
from tests.types import WithProjectPermissionsCallable
from users.models import FFAdminUser, UserPermissionGroup

now = timezone.now()
yesterday = now - timedelta(days=1)


def test_should_create_a_project(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    admin_client: APIClient,
    organisation: Organisation,
    enterprise_subscription: Subscription,
) -> None:
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = None

    project_name = "project1"
    stale_flags_limit_days = 15

    data = {
        "name": project_name,
        "organisation": organisation.id,
        "stale_flags_limit_days": stale_flags_limit_days,
    }
    url = reverse("api-v1:projects:project-list")

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert Project.objects.filter(name=project_name).count() == 1

    project = Project.objects.get(name=project_name)
    assert project.stale_flags_limit_days == stale_flags_limit_days

    assert (
        response.json()["migration_status"]
        == ProjectIdentityMigrationStatus.NOT_APPLICABLE.value
    )
    assert response.json()["use_edge_identities"] is False

    # and user is admin
    assert UserProjectPermission.objects.filter(
        user=admin_user, project__id=response.json()["id"], admin=True
    )

    # and they can get the project
    url = reverse("api-v1:projects:project-detail", args=[response.json()["id"]])
    get_project_response = admin_client.get(url)
    assert get_project_response.status_code == status.HTTP_200_OK


def test_should_create_a_project_with_admin_master_api_key_client(
    settings, organisation, admin_master_api_key_client
):
    # Given
    project_name = "project1"
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = None
    data = {"name": project_name, "organisation": organisation.id}
    url = reverse("api-v1:projects:project-list")

    # When
    response = admin_master_api_key_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert Project.objects.filter(name=project_name).count() == 1
    assert (
        response.json()["migration_status"]
        == ProjectIdentityMigrationStatus.NOT_APPLICABLE.value
    )
    assert response.json()["use_edge_identities"] is False


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_can_update_project(
    client: APIClient,
    project: Project,
    organisation: Organisation,
    enterprise_subscription: Subscription,
) -> None:
    # Given
    new_name = "New project name"
    new_stale_flags_limit_days = 15

    data = {
        "name": new_name,
        "organisation": organisation.id,
        "stale_flags_limit_days": new_stale_flags_limit_days,
    }
    url = reverse("api-v1:projects:project-detail", args=[project.id])

    # When
    response = client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == new_name
    assert response.json()["stale_flags_limit_days"] == new_stale_flags_limit_days


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_can_list_project_permission(client, project):
    # Given
    url = reverse("api-v1:projects:project-permissions")

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        len(response.json()) == 6
    )  # hard code how many permissions we expect there to be


def test_my_permissions_for_a_project_return_400_with_master_api_key(
    admin_master_api_key_client, project, organisation
):
    # Given
    url = reverse("api-v1:projects:project-my-permissions", args=[project.id])

    # When
    response = admin_master_api_key_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "This endpoint can only be used with a user and not Master API Key"
    )


def test_create_project_returns_403_if_user_is_not_organisation_admin(
    organisation: Organisation,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given

    project_name = "project1"
    data = {"name": project_name, "organisation": organisation.id}
    url = reverse("api-v1:projects:project-list")

    # When
    response = staff_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        response.json()["detail"]
        == "You do not have permission to perform this action."
    )


def test_user_with_create_project_permission_can_create_project(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-list")

    user_permission = UserOrganisationPermission.objects.create(
        organisation=organisation, user=staff_user
    )
    user_permission.permissions.add(
        OrganisationPermissionModel.objects.get(key=CREATE_PROJECT)
    )
    # When
    response = staff_client.post(
        url,
        data={"name": "some proj", "organisation": organisation.id},
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_user_with_create_project_permission_cannot_create_project_if_restricted_to_admin(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    new_organisation = Organisation.objects.create(
        name="New org", restrict_project_create_to_admin=True
    )
    user_permission = UserOrganisationPermission.objects.create(
        organisation=new_organisation, user=staff_user
    )
    create_project_permission = OrganisationPermissionModel.objects.get(
        key=CREATE_PROJECT
    )
    user_permission.permissions.add(create_project_permission)
    user_permission.save()
    url = reverse("api-v1:projects:project-list")

    # When
    response = staff_client.post(
        url,
        data={"name": "some proj", "organisation": new_organisation.id},
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_with_view_project_permission_can_view_project(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: Organisation,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    url = reverse("api-v1:projects:project-detail", args=[project.id])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_user_with_view_project_permission_can_get_their_permissions_for_a_project(
    staff_client: APIClient,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    url = reverse("api-v1:projects:project-my-permissions", args=[project.id])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_user_can_list_all_user_permissions_for_a_project(
    admin_client: APIClient,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    url = reverse("api-v1:projects:project-user-permissions-list", args=[project.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_user_can_create_new_user_permission_for_a_project(
    staff_user: FFAdminUser,
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    data = {
        "user": staff_user.id,
        "permissions": [VIEW_PROJECT, CREATE_ENVIRONMENT],
        "admin": False,
    }
    url = reverse("api-v1:projects:project-user-permissions-list", args=[project.id])
    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert sorted(response.json()["permissions"]) == sorted(data["permissions"])

    assert UserProjectPermission.objects.filter(
        user=staff_user, project=project
    ).exists()
    user_project_permission = UserProjectPermission.objects.get(
        user=staff_user, project=project
    )
    assert user_project_permission.permissions.count() == 2


def test_user_can_update_user_permission_for_a_project(
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    admin_client: APIClient,
) -> None:
    # Given
    upp = with_project_permissions([VIEW_PROJECT])
    data = {"permissions": [CREATE_FEATURE]}
    url = reverse(
        "api-v1:projects:project-user-permissions-detail",
        args=[project.id, upp.id],
    )

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    upp.refresh_from_db()
    assert CREATE_FEATURE in upp.permissions.values_list("key", flat=True)


def test_user_can_delete_user_permission_for_a_project(
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    admin_client: APIClient,
) -> None:
    # Given
    upp = with_project_permissions([VIEW_PROJECT])
    url = reverse(
        "api-v1:projects:project-user-permissions-detail",
        args=[project.id, upp.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserProjectPermission.objects.filter(id=upp.id).exists()


def test_user_can_list_all_user_group_permissions_for_a_project(
    project: Project,
    admin_client: APIClient,
    organisation: Organisation,
    staff_user: FFAdminUser,
) -> None:
    # Given
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_permission_group.users.add(staff_user)
    upgpp = UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project
    )
    upgpp.permissions.set([ProjectPermissionModel.objects.get(key=VIEW_PROJECT)])

    url = reverse(
        "api-v1:projects:project-user-group-permissions-list",
        args=[project.id],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_user_can_create_new_user_group_permission_for_a_project(
    organisation: Organisation,
    project: Project,
    staff_user: FFAdminUser,
    admin_client: APIClient,
) -> None:
    # Given
    new_group = UserPermissionGroup.objects.create(
        name="New group", organisation=organisation
    )
    new_group.users.add(staff_user)
    data = {
        "group": new_group.id,
        "permissions": [VIEW_PROJECT, CREATE_ENVIRONMENT],
        "admin": False,
    }
    url = reverse(
        "api-v1:projects:project-user-group-permissions-list",
        args=[project.id],
    )

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert sorted(response.json()["permissions"]) == sorted(data["permissions"])

    assert UserPermissionGroupProjectPermission.objects.filter(
        group=new_group, project=project
    ).exists()
    user_group_project_permission = UserPermissionGroupProjectPermission.objects.get(
        group=new_group, project=project
    )
    assert user_group_project_permission.permissions.count() == 2


def test_user_can_update_user_group_permission_for_a_project(
    admin_client: APIClient,
    project: Project,
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_permission_group.users.add(staff_user)
    upgpp = UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project
    )
    upgpp.permissions.set([ProjectPermissionModel.objects.get(key=VIEW_PROJECT)])

    url = reverse(
        "api-v1:projects:project-user-group-permissions-detail",
        args=[project.id, upgpp.id],
    )
    data = {"permissions": [CREATE_FEATURE]}

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    upgpp.refresh_from_db()
    assert CREATE_FEATURE in upgpp.permissions.values_list("key", flat=True)


def test_user_group_can_delete_user_permission_for_a_project(
    admin_client: APIClient,
    project: Project,
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_permission_group.users.add(staff_user)
    upgpp = UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project
    )
    upgpp.permissions.set([ProjectPermissionModel.objects.get(key=VIEW_PROJECT)])

    url = reverse(
        "api-v1:projects:project-user-group-permissions-detail",
        args=[project.id, upgpp.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserPermissionGroupProjectPermission.objects.filter(id=upgpp.id).exists()


def test_project_migrate_to_edge_calls_trigger_migration(
    admin_client, project, mocker, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "some_table"
    mocked_identity_migrator = mocker.patch("projects.views.IdentityMigrator")

    url = reverse("api-v1:projects:project-migrate-to-edge", args=[project.id])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    mocked_identity_migrator.assert_called_once_with(project.id)
    mocked_identity_migrator.return_value.trigger_migration.assert_called_once()


def test_project_migrate_to_edge_returns_400_if_can_migrate_is_false(
    admin_client, project, mocker, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "some_table"
    mocked_identity_migrator = mocker.patch("projects.views.IdentityMigrator")
    mocked_identity_migrator.return_value.can_migrate = False

    url = reverse("api-v1:projects:project-migrate-to-edge", args=[project.id])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mocked_identity_migrator.assert_called_once_with(project.id)
    mocked_identity_migrator.return_value.trigger_migration.assert_not_called()


def test_project_migrate_to_edge_returns_400_if_project_have_too_many_identities(
    admin_client, project, mocker, settings, identity, environment
):
    # Given
    Identity.objects.create(environment=environment, identifier="identity2")
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "some_table"
    settings.MAX_SELF_MIGRATABLE_IDENTITIES = 1
    mocked_identity_migrator = mocker.patch("projects.views.IdentityMigrator")

    url = reverse("api-v1:projects:project-migrate-to-edge", args=[project.id])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Too many identities; Please contact support"
    mocked_identity_migrator.assert_not_called()


def test_project_migrate_to_edge_returns_400_if_project_have_too_many_features(
    admin_client, project, mocker, environment, feature, multivariate_feature, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "some_table"
    project.max_features_allowed = 1
    project.save()

    mocked_identity_migrator = mocker.patch("projects.views.IdentityMigrator")

    url = reverse("api-v1:projects:project-migrate-to-edge", args=[project.id])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Project is too large; Please contact support"
    mocked_identity_migrator.assert_not_called()


def test_project_migrate_to_edge_returns_400_if_project_have_too_many_segments(
    admin_client,
    project,
    mocker,
    environment,
    feature,
    settings,
    feature_based_segment,
    segment,
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "some_table"
    project.max_segments_allowed = 1
    project.save()

    mocked_identity_migrator = mocker.patch("projects.views.IdentityMigrator")

    url = reverse("api-v1:projects:project-migrate-to-edge", args=[project.id])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Project is too large; Please contact support"
    mocked_identity_migrator.assert_not_called()


def test_project_migrate_to_edge_returns_400_if_project_have_too_many_segment_overrides(
    admin_client,
    project,
    mocker,
    environment,
    feature,
    settings,
    feature_segment,
    multivariate_feature,
    segment,
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "some_table"
    project.max_segment_overrides_allowed = 1
    project.save()

    # let's create another feature segment
    FeatureSegment.objects.create(
        feature=multivariate_feature, segment=segment, environment=environment
    )
    mocked_identity_migrator = mocker.patch("projects.views.IdentityMigrator")

    url = reverse("api-v1:projects:project-migrate-to-edge", args=[project.id])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Project is too large; Please contact support"
    mocked_identity_migrator.assert_not_called()


def test_list_project_with_uuid_filter_returns_correct_project(
    admin_client, project, mocker, settings, organisation
):
    # Given
    # another project
    Project.objects.create(name="Other project", organisation=organisation)

    base_url = reverse("api-v1:projects:project-list")
    url = f"{base_url}?uuid={project.uuid}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["uuid"] == str(project.uuid)


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_get_project_by_uuid(client, project, mocker, settings, organisation):
    # Given
    url = reverse("api-v1:projects:project-get-by-uuid", args=[str(project.uuid)])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(project.uuid)


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_can_enable_realtime_updates_for_project(
    client, project, mocker, settings, organisation
):
    # Given
    url = reverse("api-v1:projects:project-detail", args=[project.id])

    data = {
        "name": project.name,
        "organisation": organisation.id,
        "enable_realtime_updates": True,
    }

    # When
    response = client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(project.uuid)
    assert response.json()["enable_realtime_updates"] is True


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_update_project(client, project, mocker, settings, organisation):
    # Given
    url = reverse("api-v1:projects:project-detail", args=[project.id])
    feature_name_regex = r"^[a-zA-Z0-9_]+$"
    data = {
        "name": project.name,
        "organisation": organisation.id,
        "only_allow_lower_case_feature_names": False,
        "feature_name_regex": feature_name_regex,
    }

    # When
    response = client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["only_allow_lower_case_feature_names"] is False
    assert response.json()["feature_name_regex"] == feature_name_regex


@pytest.mark.parametrize(
    "client",
    (lazy_fixture("admin_client"), lazy_fixture("admin_master_api_key_client")),
)
def test_get_project_list_data(client, organisation):
    # Given
    list_url = reverse("api-v1:projects:project-list")

    project_name = "Test project"
    hide_disabled_flags = False
    enable_dynamo_db = False
    prevent_flag_defaults = True
    enable_realtime_updates = False
    only_allow_lower_case_feature_names = True

    Project.objects.create(
        name=project_name,
        organisation=organisation,
        hide_disabled_flags=hide_disabled_flags,
        enable_dynamo_db=enable_dynamo_db,
        prevent_flag_defaults=prevent_flag_defaults,
        enable_realtime_updates=enable_realtime_updates,
        only_allow_lower_case_feature_names=only_allow_lower_case_feature_names,
    )

    # When
    response = client.get(list_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == project_name
    assert response.json()[0]["hide_disabled_flags"] is hide_disabled_flags
    assert response.json()[0]["enable_dynamo_db"] is enable_dynamo_db
    assert response.json()[0]["prevent_flag_defaults"] is prevent_flag_defaults
    assert response.json()[0]["enable_realtime_updates"] is enable_realtime_updates
    assert (
        response.json()[0]["only_allow_lower_case_feature_names"]
        is only_allow_lower_case_feature_names
    )
    assert "max_segments_allowed" not in response.json()[0].keys()
    assert "max_features_allowed" not in response.json()[0].keys()
    assert "max_segment_overrides_allowed" not in response.json()[0].keys()
    assert "total_features" not in response.json()[0].keys()
    assert "total_segments" not in response.json()[0].keys()


@pytest.mark.parametrize(
    "client",
    (lazy_fixture("admin_client"), lazy_fixture("admin_master_api_key_client")),
)
def test_get_project_data_by_id(
    client: APIClient, organisation: Organisation, project: Project
) -> None:
    # Given
    url = reverse("api-v1:projects:project-detail", args=[project.id])

    num_features = 5
    num_segments = 7

    for i in range(num_features):
        Feature.objects.create(name=f"feature_{i}", project=project)

    for i in range(num_segments):
        Segment.objects.create(name=f"feature_{i}", project=project)

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["name"] == project.name
    assert response_json["max_segments_allowed"] == 100
    assert response_json["max_features_allowed"] == 400
    assert response_json["max_segment_overrides_allowed"] == 100
    assert response_json["total_features"] == num_features
    assert response_json["total_segments"] == num_segments
    assert response_json["show_edge_identity_overrides_for_feature"] is False


def test_delete_project_delete_handles_cascade_delete(
    admin_client: APIClient,
    project: Project,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    url = reverse("api-v1:projects:project-detail", args=[project.id])
    mocked_handle_cascade_delete = mocker.patch("projects.models.handle_cascade_delete")

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mocked_handle_cascade_delete.delay.assert_called_once_with(
        kwargs={"project_id": project.id}
    )
