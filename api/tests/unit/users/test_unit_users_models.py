import uuid

import pytest
from common.projects.permissions import VIEW_PROJECT
from django.db.utils import IntegrityError

from organisations.models import Organisation, OrganisationRole
from organisations.permissions.models import UserOrganisationPermission
from organisations.permissions.permissions import ORGANISATION_PERMISSIONS
from projects.models import Project
from tests.types import WithProjectPermissionsCallable
from users.models import FFAdminUser, UserPermissionGroup


def test_belongs_to__user_in_organisation__returns_true(
    admin_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    assert organisation in admin_user.organisations.all()
    # When / Then
    assert admin_user.belongs_to(organisation.id)


def test_belongs_to__user_not_in_organisation__returns_false(
    admin_user: FFAdminUser,
) -> None:
    # Given
    unaffiliated_organisation = Organisation.objects.create(name="Unaffiliated")
    # When / Then
    assert not admin_user.belongs_to(unaffiliated_organisation.id)


def test_get_permitted_projects__org_admin__returns_all_projects(
    admin_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    Project.objects.create(name="Test project 2", organisation=organisation)
    # When
    projects = admin_user.get_permitted_projects(VIEW_PROJECT)

    # Then
    assert projects.count() == 2


def test_get_permitted_projects__user_with_view_permission__returns_matching_projects(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]

    # When
    projects = staff_user.get_permitted_projects(permission_key=VIEW_PROJECT)

    # Then
    assert projects.count() == 1
    assert projects.first() == project


def test_get_admin_organisations__user_with_mixed_roles__returns_only_admin_orgs(
    admin_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    non_admin_organisation = Organisation.objects.create(name="non-admin")
    admin_user.add_organisation(non_admin_organisation, OrganisationRole.USER)

    # When
    admin_orgs = admin_user.get_admin_organisations()  # type: ignore[no-untyped-call]

    # Then
    assert organisation in admin_orgs
    assert non_admin_organisation not in admin_orgs


def test_get_permitted_environments__org_admin__returns_all_project_environments(
    admin_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given / When
    environments = admin_user.get_permitted_environments(
        "VIEW_ENVIRONMENT", project=project
    )

    # Then
    assert environments.count() == project.environments.count()


def test_get_permitted_environments__user_without_permission__returns_empty(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given / When
    environments = staff_user.get_permitted_environments(
        "VIEW_ENVIRONMENT", project=project
    )

    # Then
    assert len(list(environments)) == 0


def test_add_organisation__duplicate_membership__raises_integrity_error(
    admin_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given / When
    # Then
    with pytest.raises(IntegrityError):
        admin_user.add_organisation(organisation, OrganisationRole.USER)


def test_has_organisation_permission__org_admin__returns_true_for_all_permissions(
    admin_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given / When
    # Then
    assert ORGANISATION_PERMISSIONS
    assert all(
        admin_user.has_organisation_permission(
            organisation=organisation, permission_key=permission_key
        )
        for permission_key, _ in ORGANISATION_PERMISSIONS
    )


def test_has_organisation_permission__user_with_all_permissions__returns_true(
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    user_organisation_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    for permission_key, _ in ORGANISATION_PERMISSIONS:
        user_organisation_permission.permissions.through.objects.create(
            permissionmodel_id=permission_key,
            userorganisationpermission=user_organisation_permission,
        )

    # When / Then
    assert all(
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=permission_key
        )
        for permission_key, _ in ORGANISATION_PERMISSIONS
    )


def test_has_organisation_permission__user_without_permissions__returns_false(
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given / When
    # Then
    assert not any(
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=permission_key
        )
        for permission_key, _ in ORGANISATION_PERMISSIONS
    )


def test_add_organisation__default_group_exists__adds_user_to_default_group(
    organisation: Organisation,
    default_user_permission_group: UserPermissionGroup,
    user_permission_group: UserPermissionGroup,
) -> None:
    # Given
    user = FFAdminUser.objects.create(email=f"test{uuid.uuid4()}@example.com")

    # When
    user.add_organisation(organisation, OrganisationRole.USER)

    # Then
    assert default_user_permission_group in user.permission_groups.all()
    assert user_permission_group not in user.permission_groups.all()


def test_remove_organisation__user_in_permission_group__removes_from_group(  # type: ignore[no-untyped-def]
    user_permission_group, admin_user, organisation, default_user_permission_group
):
    # Given - two groups that belongs to the same organisation, but user
    # is only part of one(`user_permission_group`) them

    # When
    admin_user.remove_organisation(organisation)

    # Then
    # extra group did not cause any errors and the user is removed from the group
    assert user_permission_group not in admin_user.permission_groups.all()


@pytest.mark.django_db
def test_delete_user__with_orphan_organisations__deletes_orphan_orgs():  # type: ignore[no-untyped-def]
    # Given - create a couple of users
    email1 = "test1@example.com"
    email2 = "test2@example.com"
    email3 = "test3@example.com"
    user1 = FFAdminUser.objects.create(email=email1)
    user2 = FFAdminUser.objects.create(email=email2)
    user3 = FFAdminUser.objects.create(email=email3)

    # crete some organizations
    org1 = Organisation.objects.create(name="org1")
    org2 = Organisation.objects.create(name="org2")
    org3 = Organisation.objects.create(name="org3")

    # add the test user 1 to all the organizations
    org1.users.add(user1)
    org2.users.add(user1)
    org3.users.add(user1)

    # add test user 2 to org2 and user 3 to to org1
    org2.users.add(user2)
    org1.users.add(user3)

    # Configuration: org1: [user1, user3], org2: [user1, user2], org3: [user1]

    # When
    user2.delete(delete_orphan_organisations=True)

    # Then
    assert not FFAdminUser.objects.filter(email=email2).exists()

    # All organisations remain since user 2 has org2 as only organization and it has 2 users
    assert Organisation.objects.filter(name="org3").count() == 1
    assert Organisation.objects.filter(name="org1").count() == 1
    assert Organisation.objects.filter(name="org2").count() == 1

    # Delete user1
    user1.delete(delete_orphan_organisations=True)
    assert not FFAdminUser.objects.filter(email=email1).exists()

    # organization org3 and org2 are deleted since its only user is user1
    assert Organisation.objects.filter(name="org3").count() == 0
    assert Organisation.objects.filter(name="org2").count() == 0

    # org1 remain
    assert Organisation.objects.filter(name="org1").count() == 1

    # user3 remain
    assert FFAdminUser.objects.filter(email=email3).exists()

    # Delete user3
    user3.delete(delete_orphan_organisations=False)
    assert not FFAdminUser.objects.filter(email=email3).exists()
    assert Organisation.objects.filter(name="org1").count() == 1


def test_email_domain__valid_email__returns_domain():  # type: ignore[no-untyped-def]
    # Given / When
    # Then
    assert FFAdminUser(email="test@example.com").email_domain == "example.com"
