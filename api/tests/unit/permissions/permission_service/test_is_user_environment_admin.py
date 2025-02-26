import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from permissions.permission_service import is_user_environment_admin


def test_is_user_environment_admin_returns_true_for_org_admin(admin_user, environment):  # type: ignore[no-untyped-def]  # noqa: E501
    assert is_user_environment_admin(admin_user, environment) is True


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
    ],
)
def test_is_user_environment_admin_returns_true_for_project_admin(  # type: ignore[no-untyped-def]
    test_user, environment, project_admin
):
    # Then
    assert is_user_environment_admin(test_user, environment) is True


@pytest.mark.parametrize(
    "environment_admin",
    [
        (lazy_fixture("environment_admin_via_user_permission")),
        (lazy_fixture("environment_admin_via_user_permission_group")),
    ],
)
def test_is_user_environment_admin_returns_true_for_environment_admin(  # type: ignore[no-untyped-def]
    test_user, environment, environment_admin
):
    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_false_for_user_with_no_permission(  # type: ignore[no-untyped-def]
    test_user,
    environment,
):
    assert is_user_environment_admin(test_user, environment) is False


def test_is_user_environment_admin_returns_false_for_user_with_admin_permission_of_other_org(  # type: ignore[no-untyped-def]  # noqa: E501
    admin_user,
    organisation_two_project_one_environment_one,
):
    assert (
        is_user_environment_admin(
            admin_user, organisation_two_project_one_environment_one
        )
        is False
    )


def test_is_user_environment_admin_returns_false_for_user_with_admin_permission_of_other_environment(  # type: ignore[no-untyped-def]  # noqa: E501
    django_user_model,
    environment,
    user_project_permission,
    user_environment_permission,
    user_project_permission_group,
    user_environment_permission_group,
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    # First, let's give the user admin permission
    user_project_permission.admin = True
    user_project_permission.save()

    user_environment_permission.admin = True
    user_environment_permission.save()

    # let's give the user admin permission using a group
    user_project_permission_group.admin = True
    user_project_permission_group.save()

    user_environment_permission_group.admin = True
    user_environment_permission_group.save()

    # Then - the user should not be admin of the environment
    assert is_user_environment_admin(user, environment) is False
