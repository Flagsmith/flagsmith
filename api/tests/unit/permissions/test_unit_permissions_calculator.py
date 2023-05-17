import pytest

from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
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
from organisations.permissions.permissions import CREATE_PROJECT
from permissions.permissions_calculator import (
    get_environment_permission_data,
    get_organisation_permission_data,
    get_project_permission_data,
)
from projects.models import (
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions import CREATE_ENVIRONMENT, VIEW_PROJECT
from users.models import UserPermissionGroup


@pytest.mark.parametrize(
    (
        "user_permissions, user_admin, group_permissions, group_admin,"
        " expected_permissions, expected_admin"
    ),
    (
        (set(), False, set(), False, set(), False),
        (
            {VIEW_PROJECT},
            False,
            set(),
            False,
            {VIEW_PROJECT},
            False,
        ),
        (
            set(),
            False,
            {VIEW_PROJECT},
            False,
            {VIEW_PROJECT},
            False,
        ),
        (
            set(),
            False,
            set(),
            False,
            set(),
            False,
        ),
        (set(), True, set(), False, set(), True),
        (set(), False, set(), True, set(), True),
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
        (set(), True, set(), True, set(), True),
    ),
)
def test_project_permissions_calculator_get_permission_data(
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
        (set(), False, set(), False, set(), False),
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
        (set(), True, set(), True, set(), True),
    ),
)
def test_environment_permissions_calculator_get_permission_data(
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
        environment.id, user_id=user.id
    )

    # Then
    assert user_permission_data.admin == expected_admin
    assert user_permission_data.permissions == expected_permissions


@pytest.mark.parametrize(
    (
        "user_permissions, user_admin, group_permissions, "
        "expected_permissions, expected_admin"
    ),
    (
        (set(), False, set(), set(), False),
        (set(), True, set(), set(), True),
        (
            {CREATE_PROJECT},
            False,
            set(),
            {CREATE_PROJECT},
            False,
        ),
        (
            set(),
            False,
            {CREATE_PROJECT},
            {CREATE_PROJECT},
            False,
        ),
        (
            set(),
            False,
            set(),
            set(),
            False,
        ),
        (
            {CREATE_PROJECT},
            False,
            set(),
            {CREATE_PROJECT},
            False,
        ),
    ),
)
def test_organisation_permissions_calculator_get_permission_data(
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
