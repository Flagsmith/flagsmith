import pytest
from common.environments.permissions import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import CREATE_ENVIRONMENT, DELETE_FEATURE, VIEW_PROJECT

from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import OrganisationRole
from organisations.permissions.models import (
    OrganisationPermissionModel,
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
)
from permissions.permissions_calculator import (
    GroupData,
    GroupPermissionData,
    PermissionData,
    RoleData,
    RolePermissionData,
    UserPermissionData,
    get_environment_permission_data,
    get_organisation_permission_data,
    get_project_permission_data,
)
from projects.models import (
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.models import UserPermissionGroup


@pytest.mark.parametrize(
    (
        "user_permissions, user_admin, group_permissions, group_admin,"
        " expected_permissions, expected_admin"
    ),
    (
        (set(), False, set(), False, set(), False),
        (set(), True, set(), False, set(), True),
        (set(), False, set(), True, set(), True),
        (set(), True, set(), True, set(), True),
        ({VIEW_PROJECT}, False, set(), False, {VIEW_PROJECT}, False),
        (set(), False, {VIEW_PROJECT}, False, {VIEW_PROJECT}, False),
        (
            {VIEW_PROJECT, CREATE_ENVIRONMENT},
            False,
            set(),
            False,
            {VIEW_PROJECT, CREATE_ENVIRONMENT},
            False,
        ),
        (
            {CREATE_ENVIRONMENT},
            False,
            {VIEW_PROJECT},
            False,
            {VIEW_PROJECT, CREATE_ENVIRONMENT},
            False,
        ),
    ),
)
def test_project_permissions_calculator_get_permission_data(  # type: ignore[no-untyped-def]
    project,
    organisation,
    django_user_model,
    user_permissions,
    user_admin,
    group_permissions,
    group_admin,
    expected_permissions,
    expected_admin,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.USER)

    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(user)

    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=project, admin=user_admin
    )
    group_project_permission = UserPermissionGroupProjectPermission.objects.create(
        group=group, project=project, admin=group_admin
    )

    project_permissions = {pm.key: pm for pm in ProjectPermissionModel.objects.all()}

    for permission_key in user_permissions:
        user_project_permission.permissions.add(project_permissions[permission_key])

    for permission_key in group_permissions:
        group_project_permission.permissions.add(project_permissions[permission_key])

    # When
    user_permission_data = get_project_permission_data(project.id, user_id=user.id)

    # Then
    assert user_permission_data.admin == expected_admin
    assert user_permission_data.permissions == expected_permissions


@pytest.mark.parametrize(
    (
        "user_permissions, user_admin, group_permissions, group_admin, "
        "expected_permissions, expected_admin"
    ),
    (
        (set(), False, set(), False, set(), False),
        (set(), True, set(), True, set(), True),
        (
            {VIEW_ENVIRONMENT},
            False,
            set(),
            False,
            {VIEW_ENVIRONMENT},
            False,
        ),
        (
            set(),
            False,
            {VIEW_ENVIRONMENT},
            False,
            {VIEW_ENVIRONMENT},
            False,
        ),
        (set(), True, set(), False, set(), True),
        (set(), False, set(), True, set(), True),
        (
            {VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE},
            False,
            set(),
            False,
            {VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE},
            False,
        ),
        (
            {UPDATE_FEATURE_STATE},
            False,
            {VIEW_ENVIRONMENT},
            False,
            {VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE},
            False,
        ),
    ),
)
def test_environment_permissions_calculator_get_permission_data(  # type: ignore[no-untyped-def]
    environment,
    organisation,
    django_user_model,
    user_permissions,
    user_admin,
    group_permissions,
    group_admin,
    expected_permissions,
    expected_admin,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.USER)

    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(user)

    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=user, environment=environment, admin=user_admin
    )
    group_environment_permission = (
        UserPermissionGroupEnvironmentPermission.objects.create(
            group=group, environment=environment, admin=group_admin
        )
    )

    environment_permissions = {
        pm.key: pm for pm in EnvironmentPermissionModel.objects.all()
    }

    for permission_key in user_permissions:
        user_environment_permission.permissions.add(
            environment_permissions[permission_key]
        )

    for permission_key in group_permissions:
        group_environment_permission.permissions.add(
            environment_permissions[permission_key]
        )

    # When
    user_permission_data = get_environment_permission_data(
        environment=environment, user=user
    )

    # Then
    assert user_permission_data.admin == expected_admin
    assert user_permission_data.permissions == expected_permissions


def test_environment_permissions_calculator_returns_admin_for_project_admin(  # type: ignore[no-untyped-def]
    environment, project, organisation, django_user_model
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.USER)

    UserProjectPermission.objects.create(user=user, project=project, admin=True)

    # When
    user_permission_data = get_environment_permission_data(
        environment=environment, user=user
    )

    # Then
    assert user_permission_data.admin is True


@pytest.mark.parametrize(
    (
        "user_permissions, user_admin, group_permissions, "
        "expected_permissions, expected_admin"
    ),
    (
        (set(), False, set(), set(), False),
        (set(), True, set(), set(), True),
        ({CREATE_PROJECT}, False, set(), {CREATE_PROJECT}, False),
        (set(), False, {CREATE_PROJECT}, {CREATE_PROJECT}, False),
        ({CREATE_PROJECT}, False, set(), {CREATE_PROJECT}, False),
        (
            {CREATE_PROJECT},
            False,
            {MANAGE_USER_GROUPS},
            {CREATE_PROJECT, MANAGE_USER_GROUPS},
            False,
        ),
    ),
)
def test_organisation_permissions_calculator_get_permission_data(  # type: ignore[no-untyped-def]
    organisation,
    django_user_model,
    user_permissions,
    user_admin,
    group_permissions,
    expected_permissions,
    expected_admin,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")

    org_role = OrganisationRole.ADMIN if user_admin else OrganisationRole.USER

    user.add_organisation(organisation, org_role)

    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(user)

    user_organisation_permission = UserOrganisationPermission.objects.create(
        user=user, organisation=organisation
    )
    group_organisation_permission = (
        UserPermissionGroupOrganisationPermission.objects.create(
            group=group, organisation=organisation
        )
    )

    organisation_permissions = {
        pm.key: pm for pm in OrganisationPermissionModel.objects.all()
    }

    for permission_key in user_permissions:
        user_organisation_permission.permissions.add(
            organisation_permissions[permission_key]
        )

    for permission_key in group_permissions:
        group_organisation_permission.permissions.add(
            organisation_permissions[permission_key]
        )

    # When
    user_permission_data = get_organisation_permission_data(organisation.id, user=user)

    # Then
    assert user_permission_data.admin == expected_admin
    assert user_permission_data.permissions == expected_permissions


def test_permission_data_to_detailed_permissions_data() -> None:
    # Given
    user_permission_data = UserPermissionData(admin=True, permissions={CREATE_PROJECT})
    # two groups with some overallping permissions
    group_one_permission_data = GroupPermissionData(
        admin=True,
        group=GroupData(id=1, name="group_one"),
        permissions={CREATE_PROJECT, MANAGE_USER_GROUPS, VIEW_PROJECT},
    )
    group_two_permission_data = GroupPermissionData(
        admin=True,
        group=GroupData(id=1, name="group_one"),
        permissions={VIEW_PROJECT},
    )
    # two roles with same permissions with different tags
    role_one_permission_data = RolePermissionData(
        admin=True,
        role=RoleData(id=1, name="role_one", tags={1, 2}),
        permissions={DELETE_FEATURE},
    )
    role_two_permission_data = RolePermissionData(
        admin=False,
        role=RoleData(id=2, name="role_two", tags={3, 4}),
        permissions={DELETE_FEATURE},
    )
    # third role without tags
    role_three_permission_data = RolePermissionData(
        admin=False,
        role=RoleData(id=3, name="role_three", tags=set()),
        permissions={VIEW_PROJECT},
    )

    # When
    detailed_permission_data = PermissionData(
        user=user_permission_data,
        groups=[group_one_permission_data, group_two_permission_data],
        roles=[
            role_one_permission_data,
            role_two_permission_data,
            role_three_permission_data,
        ],
    ).to_detailed_permissions_data()

    # Then
    assert detailed_permission_data.admin is True
    assert len(detailed_permission_data.permissions) == 4

    assert detailed_permission_data.permissions[0].permission_key == CREATE_PROJECT
    assert detailed_permission_data.permissions[0].is_directly_granted is True
    assert detailed_permission_data.permissions[0].derived_from.groups == [
        group_one_permission_data.group
    ]
    assert detailed_permission_data.permissions[0].derived_from.roles == []

    assert detailed_permission_data.permissions[1].permission_key == MANAGE_USER_GROUPS
    assert detailed_permission_data.permissions[1].is_directly_granted is False
    assert detailed_permission_data.permissions[1].derived_from.groups == [
        group_one_permission_data.group
    ]
    assert detailed_permission_data.permissions[1].derived_from.roles == []

    assert detailed_permission_data.permissions[2].permission_key == VIEW_PROJECT
    assert detailed_permission_data.permissions[2].is_directly_granted is False
    assert detailed_permission_data.permissions[2].derived_from.groups == [
        group_one_permission_data.group,
        group_two_permission_data.group,
    ]
    assert detailed_permission_data.permissions[2].derived_from.roles == [
        role_three_permission_data.role
    ]

    assert detailed_permission_data.permissions[3].permission_key == DELETE_FEATURE
    assert detailed_permission_data.permissions[3].is_directly_granted is False
    assert detailed_permission_data.permissions[3].derived_from.groups == []
    assert detailed_permission_data.permissions[3].derived_from.roles == [
        role_one_permission_data.role,
        role_two_permission_data.role,
    ]
