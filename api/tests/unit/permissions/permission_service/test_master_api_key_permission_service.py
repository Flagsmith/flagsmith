import pytest
from pytest_lazyfixture import lazy_fixture

from environments.permissions.models import EnvironmentPermissionModel
from organisations.permissions.models import OrganisationPermissionModel
from permissions.permission_service import (
    get_permitted_environments_for_master_api_key,
    get_permitted_projects_for_master_api_key,
    is_master_api_key_environment_admin,
    is_master_api_key_project_admin,
    master_api_key_has_organisation_permission,
)
from projects.models import ProjectPermissionModel


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
def test_is_master_api_key_project_admin(
    for_project,
    for_master_api_key,
    expected_is_admin,
    admin_master_api_key,
    master_api_key,
):
    assert (
        is_master_api_key_project_admin(for_master_api_key, for_project)
        is expected_is_admin
    )


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
def test_is_master_api_key_environment_admin(
    for_environment,
    for_master_api_key,
    expected_is_admin,
    organisation_two_project_one_environment_one,
):
    assert (
        is_master_api_key_environment_admin(for_master_api_key, for_environment)
        is expected_is_admin
    )


@pytest.mark.parametrize(
    "for_project, for_master_api_key, expected_count",
    [
        (lazy_fixture("project"), lazy_fixture("admin_master_api_key_object"), 1),
        (lazy_fixture("project"), lazy_fixture("master_api_key_object"), 0),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("master_api_key_object"),
            0,
        ),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("admin_master_api_key_object"),
            0,
        ),
    ],
)
def test_get_permitted_projects_for_master_api_key(
    for_project,
    for_master_api_key,
    expected_count,
):
    # When
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            get_permitted_projects_for_master_api_key(
                for_master_api_key, permission
            ).count()
            == expected_count
        )


@pytest.mark.parametrize(
    "for_project, for_master_api_key, expected_count",
    [
        (lazy_fixture("project"), lazy_fixture("admin_master_api_key_object"), 2),
        (lazy_fixture("project"), lazy_fixture("master_api_key_object"), 0),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("master_api_key_object"),
            0,
        ),
        (
            lazy_fixture("organisation_two_project_one"),
            lazy_fixture("admin_master_api_key_object"),
            0,
        ),
    ],
)
def test_get_permitted_environments_for_master_api_key(
    for_project,
    for_master_api_key,
    expected_count,
    environment,
    environment_two,
    organisation_two_project_one_environment_one,
    admin_master_api_key,
    master_api_key,
):
    # When
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            get_permitted_environments_for_master_api_key(
                for_master_api_key, for_project, permission
            ).count()
            == expected_count
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
def test_master_api_key_has_organisation_permission(
    for_organisation,
    for_master_api_key,
    expected_has_permission,
    admin_master_api_key,
    master_api_key,
):
    # When
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            master_api_key_has_organisation_permission(
                for_master_api_key, for_organisation, permission
            )
            is expected_has_permission
        )
