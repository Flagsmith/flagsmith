import pytest
from common.environments.permissions import (
    CREATE_CHANGE_REQUEST,
    MANAGE_IDENTITIES,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import CREATE_ENVIRONMENT, VIEW_PROJECT
from pytest_mock import MockerFixture

from environments.models import Environment
from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import Organisation, OrganisationRole
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
    Project,
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.models import FFAdminUser, UserPermissionGroup


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
    user_permission_data = get_project_permission_data(project, user=user)

    # Then
    assert user_permission_data.admin == expected_admin
    assert user_permission_data.permissions == expected_permissions
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == []
    assert user_permission_data.inherited_admin_roles == []


def test_project_permissions_calculator_get_permission_data_for_organisation_admin(
    project: Project, organisation: Organisation, django_user_model: FFAdminUser
) -> None:
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.ADMIN)

    # When
    user_permission_data = get_project_permission_data(project, user=user)

    # Then
    assert user_permission_data.admin is True
    assert user_permission_data.permissions == set()
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == []
    assert user_permission_data.inherited_admin_roles == []


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
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == []
    assert user_permission_data.inherited_admin_roles == []


def test_environment_permissions_calculator_get_permission_data_for_direct_project_admin(
    environment: Environment,
    project: Project,
    organisation: Organisation,
    django_user_model: FFAdminUser,
) -> None:
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


def test_environment_permissions_calculator_get_permission_data_for_project_admin_through_group(
    environment: Environment,
    project: Project,
    organisation: Organisation,
    django_user_model: FFAdminUser,
) -> None:
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.USER)
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(user)

    UserPermissionGroupProjectPermission.objects.create(
        group=group, project=project, admin=True
    )
    # When
    user_permission_data = get_environment_permission_data(
        environment=environment, user=user
    )

    # Then
    assert user_permission_data.admin is True
    assert user_permission_data.permissions == set()
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == [
        GroupPermissionData(
            group=GroupData(id=group.id, name=group.name), admin=True, permissions=set()
        )
    ]
    assert user_permission_data.inherited_admin_roles == []


def test_environment_permissions_calculator_get_permission_data_for_project_admin_through_role(
    environment: Environment,
    project: Project,
    organisation: Organisation,
    django_user_model: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.USER)

    admin_role = RolePermissionData(
        role=RoleData(id=1, name="Admin Role", tags=set()),
        admin=True,
        permissions=set(),
    )
    non_admin_role = RolePermissionData(
        role=RoleData(id=2, name="View only Role", tags=set()),
        admin=False,
        permissions={VIEW_PROJECT},
    )
    mocker.patch(
        "permissions.permissions_calculator.get_roles_permission_data_for_project",
        return_value=[
            non_admin_role,
            admin_role,
        ],
    )
    # When
    user_permission_data = get_environment_permission_data(
        environment=environment, user=user
    )

    # Then
    assert user_permission_data.admin is True
    assert user_permission_data.permissions == set()
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == []
    assert user_permission_data.inherited_admin_roles == [admin_role]


def test_environment_permissions_calculator_get_permission_data_for_organisation_admin(
    environment: Environment,
    organisation: Organisation,
    django_user_model: FFAdminUser,
) -> None:
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.ADMIN)

    # When
    user_permission_data = get_environment_permission_data(
        environment=environment, user=user
    )

    # Then
    assert user_permission_data.admin is True
    assert user_permission_data.permissions == set()
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == []
    assert user_permission_data.inherited_admin_roles == []


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
    assert user_permission_data.admin_override is False
    assert user_permission_data.inherited_admin_groups == []
    assert user_permission_data.inherited_admin_roles == []


def test_permission_data_to_detailed_permissions_data() -> None:
    # Given
    user_permission_data = UserPermissionData(
        admin=True, permissions={CREATE_CHANGE_REQUEST}
    )
    # two groups with some overallping permissions
    group_one_permission_data = GroupPermissionData(
        admin=True,
        group=GroupData(id=1, name="group_one"),
        permissions={CREATE_CHANGE_REQUEST, VIEW_ENVIRONMENT},
    )
    group_two_permission_data = GroupPermissionData(
        admin=True,
        group=GroupData(id=2, name="group_two"),
        permissions={VIEW_ENVIRONMENT, MANAGE_IDENTITIES},
    )
    # another inherited admin group
    inherited_admin_group_permission_data = GroupPermissionData(
        admin=True,
        group=GroupData(id=3, name="group_three"),
        permissions={MANAGE_IDENTITIES, VIEW_ENVIRONMENT},
    )

    # two roles with same permissions with different tags
    role_one_permission_data = RolePermissionData(
        admin=True,
        role=RoleData(id=1, name="role_one", tags={1, 2}),
        permissions={UPDATE_FEATURE_STATE},
    )
    role_two_permission_data = RolePermissionData(
        admin=False,
        role=RoleData(id=2, name="role_two", tags={3, 4}),
        permissions={UPDATE_FEATURE_STATE},
    )
    # third role without tags
    role_three_permission_data = RolePermissionData(
        admin=False,
        role=RoleData(id=3, name="role_three", tags=set()),
        permissions={VIEW_ENVIRONMENT},
    )
    # another inherited admin role
    inherited_admin_role_permission_data = RolePermissionData(
        admin=True,
        role=RoleData(id=4, name="role_four", tags=set()),
        permissions={MANAGE_IDENTITIES, VIEW_ENVIRONMENT},
    )

    expected_permissions = {
        CREATE_CHANGE_REQUEST: {
            "is_directly_granted": True,
            "derived_from": {
                "groups": [group_one_permission_data.group],
                "roles": [],
            },
        },
        VIEW_ENVIRONMENT: {
            "is_directly_granted": False,
            "derived_from": {
                "groups": [
                    group_one_permission_data.group,
                    group_two_permission_data.group,
                ],
                "roles": [role_three_permission_data.role],
            },
        },
        MANAGE_IDENTITIES: {
            "is_directly_granted": False,
            "derived_from": {
                "groups": [group_two_permission_data.group],
                "roles": [],
            },
        },
        UPDATE_FEATURE_STATE: {
            "is_directly_granted": False,
            "derived_from": {
                "groups": [],
                "roles": [
                    role_one_permission_data.role,
                    role_two_permission_data.role,
                ],
            },
        },
    }

    # When
    detailed_permission_data = PermissionData(
        user=user_permission_data,
        groups=[group_one_permission_data, group_two_permission_data],
        inherited_admin_groups=[inherited_admin_group_permission_data],
        inherited_admin_roles=[inherited_admin_role_permission_data],
        roles=[
            role_one_permission_data,
            role_two_permission_data,
            role_three_permission_data,
        ],
    ).to_detailed_permissions_data()
    # Then

    assert len(detailed_permission_data.permissions) == 4
    for permission in detailed_permission_data.permissions:
        assert permission.permission_key in expected_permissions
        expected = expected_permissions[permission.permission_key]
        assert permission.is_directly_granted == expected["is_directly_granted"]
        assert permission.derived_from.groups == expected["derived_from"]["groups"]  # type: ignore[index]
        assert permission.derived_from.roles == expected["derived_from"]["roles"]  # type: ignore[index]

    assert detailed_permission_data.admin is True
    assert detailed_permission_data.is_directly_granted is True

    assert detailed_permission_data.derived_from.groups == [
        inherited_admin_group_permission_data.group,
        group_one_permission_data.group,
        group_two_permission_data.group,
    ]
    assert detailed_permission_data.derived_from.roles == [
        inherited_admin_role_permission_data.role,
        role_one_permission_data.role,
    ]
