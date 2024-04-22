import pytest
from pytest_lazyfixture import lazy_fixture

from api_keys.models import MasterAPIKey
from api_keys.user import APIKeyUser
from environments.permissions.models import EnvironmentPermissionModel
from organisations.models import Organisation, OrganisationRole
from organisations.permissions.models import OrganisationPermissionModel
from projects.models import ProjectPermissionModel


def test_is_authenticated(master_api_key_object):
    # Given
    user = APIKeyUser(master_api_key_object)

    # Then
    assert user.is_authenticated is True


@pytest.mark.parametrize(
    "for_organisation, expected_result",
    [
        (lazy_fixture("organisation"), True),
        (lazy_fixture("organisation_two"), False),
    ],
)
def test_belongs_to(for_organisation, expected_result, master_api_key_object):
    # Given
    user = APIKeyUser(master_api_key_object)

    # Then
    assert user.belongs_to(for_organisation.id) == expected_result


@pytest.mark.parametrize(
    "for_project, for_master_api_key, expected_is_admin",
    [
        (lazy_fixture("project"), lazy_fixture("admin_master_api_key_object"), True),
        (lazy_fixture("project"), lazy_fixture("master_api_key_object"), False),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("admin_master_api_key_object"),
            False,
        ),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("master_api_key_object"),
            False,
        ),
    ],
)
def test_is_project_admin(
    for_project,
    for_master_api_key,
    expected_is_admin,
    admin_master_api_key,
    master_api_key,
):
    # Given
    user = APIKeyUser(for_master_api_key)

    # Then
    assert user.is_project_admin(for_project) is expected_is_admin


@pytest.mark.parametrize(
    "for_environment, for_master_api_key, expected_is_admin",
    [
        (
            lazy_fixture("environment"),
            lazy_fixture("admin_master_api_key_object"),
            True,
        ),
        (lazy_fixture("environment"), lazy_fixture("master_api_key_object"), False),
        (
            lazy_fixture("organisation_two_project_one_environment_one"),
            lazy_fixture("admin_master_api_key_object"),
            False,
        ),
        (
            lazy_fixture("organisation_two_project_one_environment_one"),
            lazy_fixture("master_api_key_object"),
            False,
        ),
    ],
)
def test_is_environment_admin(
    for_environment,
    for_master_api_key,
    expected_is_admin,
    organisation_two_project_one_environment_one,
):
    # Given
    user = APIKeyUser(for_master_api_key)

    # Then
    assert user.is_environment_admin(for_environment) is expected_is_admin


@pytest.mark.parametrize(
    "for_project, for_master_api_key, expected_has_permission",
    [
        (lazy_fixture("project"), lazy_fixture("admin_master_api_key_object"), True),
        (lazy_fixture("project"), lazy_fixture("master_api_key_object"), False),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("master_api_key_object"),
            False,
        ),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("admin_master_api_key_object"),
            False,
        ),
    ],
)
def test_has_project_permission(
    for_project, for_master_api_key, expected_has_permission
):
    # Given
    user = APIKeyUser(for_master_api_key)

    # When
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            user.has_project_permission(permission, for_project)
            is expected_has_permission
        )


@pytest.mark.parametrize(
    "for_environment, for_master_api_key, expected_has_permission",
    [
        (
            lazy_fixture("environment"),
            lazy_fixture("admin_master_api_key_object"),
            True,
        ),
        (lazy_fixture("environment"), lazy_fixture("master_api_key_object"), False),
        (
            lazy_fixture("organisation_two_project_one_environment_one"),
            lazy_fixture("admin_master_api_key_object"),
            False,
        ),
        (
            lazy_fixture("organisation_two_project_one_environment_one"),
            lazy_fixture("master_api_key_object"),
            False,
        ),
    ],
)
def test_has_environment_permission(
    for_environment, for_master_api_key, expected_has_permission
):
    # Given
    user = APIKeyUser(for_master_api_key)

    # When
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            user.has_environment_permission(permission, for_environment)
            is expected_has_permission
        )


@pytest.mark.parametrize(
    "for_organisation, for_master_api_key, expected_has_permission",
    [
        (
            lazy_fixture("organisation"),
            lazy_fixture("admin_master_api_key_object"),
            True,
        ),
        (lazy_fixture("organisation"), lazy_fixture("master_api_key_object"), False),
        (
            lazy_fixture("organisation_two"),
            lazy_fixture("master_api_key_object"),
            False,
        ),
        (
            lazy_fixture("organisation_two"),
            lazy_fixture("admin_master_api_key_object"),
            False,
        ),
    ],
)
def test_has_organisation_permission(
    for_organisation, for_master_api_key, expected_has_permission
):
    # Given
    user = APIKeyUser(for_master_api_key)

    # When
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        user.has_organisation_permission(
            for_organisation, permission
        ) is expected_has_permission


@pytest.mark.parametrize(
    "for_project, for_master_api_key, expected_project",
    [
        (
            lazy_fixture("project"),
            lazy_fixture("admin_master_api_key_object"),
            lazy_fixture("project"),
        ),
        (lazy_fixture("project"), lazy_fixture("master_api_key_object"), None),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("master_api_key_object"),
            None,
        ),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("admin_master_api_key_object"),
            None,
        ),
    ],
)
def test_get_permitted_projects(for_project, for_master_api_key, expected_project):
    # Given
    user = APIKeyUser(for_master_api_key)

    # When
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        projects = user.get_permitted_projects(permission)

        # Then
        if expected_project is None:
            assert projects.count() == 0
        else:
            assert projects.count() == 1
            assert projects.first() == expected_project


@pytest.mark.parametrize(
    "for_project, for_master_api_key, expected_environment",
    [
        (
            lazy_fixture("project"),
            lazy_fixture("admin_master_api_key_object"),
            lazy_fixture("environment"),
        ),
        (lazy_fixture("project"), lazy_fixture("master_api_key_object"), None),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("master_api_key_object"),
            None,
        ),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("admin_master_api_key_object"),
            None,
        ),
    ],
)
def test_get_permitted_environments(
    for_project,
    for_master_api_key,
    expected_environment,
    environment,
    organisation_two_project_one_environment_one,
):
    # Given
    user = APIKeyUser(for_master_api_key)

    # When
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        environments = user.get_permitted_environments(permission, for_project)

        # Then
        if expected_environment is None:
            assert environments.count() == 0
        else:
            assert environments.count() == 1
            assert environments.first() == expected_environment


def test_is_organisation_admin_for_admin_key(
    admin_master_api_key_object: MasterAPIKey,
    organisation: Organisation,
    organisation_two: Organisation,
) -> None:
    # Given
    user = APIKeyUser(admin_master_api_key_object)

    # Then
    # Return True for the associated organisation
    assert user.is_organisation_admin(organisation) is True
    assert user.is_organisation_admin(organisation.id) is True

    # Returns False for other organisation
    assert user.is_organisation_admin(organisation_two) is False
    assert user.is_organisation_admin(organisation_two.id) is False


def test_is_organisation_admin_for_non_admin_key(
    master_api_key_object: MasterAPIKey,
    organisation: Organisation,
    organisation_two: Organisation,
) -> None:
    # Given
    user = APIKeyUser(master_api_key_object)

    # Then
    assert user.is_organisation_admin(organisation) is False
    assert user.is_organisation_admin(organisation.id) is False

    assert user.is_organisation_admin(organisation_two) is False
    assert user.is_organisation_admin(organisation_two.id) is False


def test_organisation_property(
    master_api_key_object: MasterAPIKey,
    organisation: Organisation,
):
    # Given
    user = APIKeyUser(master_api_key_object)

    # When
    organisations = user.organisations

    # Then
    assert organisations.count() == 1
    assert organisations.first().id == organisation.id


def test_get_organisation_role_for_admin_key(
    admin_master_api_key_object: MasterAPIKey,
    organisation: Organisation,
    organisation_two: Organisation,
) -> None:
    # Given
    user = APIKeyUser(admin_master_api_key_object)

    # When/Then
    # Returns ADMIN for the associated organisation
    assert user.get_organisation_role(organisation) == OrganisationRole.ADMIN.value

    # Returns None for other organisation
    assert user.get_organisation_role(organisation_two) is None


def test_get_organisation_role_for_non_admin_key(
    master_api_key_object: MasterAPIKey,
    organisation: Organisation,
    organisation_two: Organisation,
) -> None:
    # Given
    user = APIKeyUser(master_api_key_object)

    # When/Then
    # Returns USER for the associated organisation
    assert user.get_organisation_role(organisation) == OrganisationRole.USER.value

    # Returns None for other organisation
    assert user.get_organisation_role(organisation_two) is None
