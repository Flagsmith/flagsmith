import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import (
    Organisation,
    OrganisationRole,
    UserOrganisation,
)
from projects.models import Project
from tests.types import WithOrganisationPermissionsCallable
from users.models import FFAdminUser


@pytest.fixture()
def deactivated_staff_user(
    organisation: Organisation, staff_user: FFAdminUser
) -> FFAdminUser:
    staff_user.set_organisation_membership_active(organisation, is_active=False)
    return staff_user


def test_user_organisation__default__is_active(
    organisation: Organisation, staff_user: FFAdminUser
) -> None:
    # Given
    # An organisation with a freshly added member.

    # When
    user_organisation = UserOrganisation.objects.get(
        user=staff_user, organisation=organisation
    )

    # Then
    assert user_organisation.is_active is True


def test_num_seats__deactivated_membership__is_not_counted(
    organisation: Organisation,
    admin_user: FFAdminUser,
    deactivated_staff_user: FFAdminUser,
) -> None:
    # Given
    # The organisation fixture has two members, one of which is now deactivated.

    # When
    num_seats = organisation.num_seats

    # Then
    assert num_seats == 1


def test_over_plan_seats_limit__deactivated_membership__is_not_counted(
    organisation: Organisation, deactivated_staff_user: FFAdminUser
) -> None:
    # Given
    organisation.subscription.max_seats = 1
    organisation.subscription.save()

    # When
    over_plan_seats_limit = organisation.over_plan_seats_limit()

    # Then
    assert over_plan_seats_limit is False


@pytest.mark.saas_mode
def test_set_organisation_membership_active__reactivate_over_seat_limit__is_allowed(
    organisation: Organisation,
    deactivated_staff_user: FFAdminUser,
) -> None:
    # Given
    # Reactivation is driven by an external identity provider over SCIM, so it
    # deliberately goes over the seat limit rather than failing the call.
    organisation.subscription.max_seats = 1
    organisation.subscription.save()

    # When
    deactivated_staff_user.set_organisation_membership_active(
        organisation, is_active=True
    )

    # Then
    assert deactivated_staff_user.belongs_to(organisation.id) is True
    assert organisation.num_seats == 2
    assert organisation.over_plan_seats_limit() is True


def test_set_organisation_membership_active__reactivate__restores_access(
    organisation: Organisation, deactivated_staff_user: FFAdminUser
) -> None:
    # Given
    assert deactivated_staff_user.belongs_to(organisation.id) is False

    # When
    deactivated_staff_user.set_organisation_membership_active(
        organisation, is_active=True
    )

    # Then
    assert deactivated_staff_user.belongs_to(organisation.id) is True
    assert organisation.num_seats == 2


def test_belongs_to__deactivated_membership__returns_false(
    organisation: Organisation, deactivated_staff_user: FFAdminUser
) -> None:
    # Given
    # A user whose membership of the organisation has been deactivated.

    # When
    belongs_to = deactivated_staff_user.belongs_to(organisation.id)

    # Then
    assert belongs_to is False


def test_is_organisation_admin__deactivated_membership__returns_false(
    organisation: Organisation, admin_user: FFAdminUser
) -> None:
    # Given
    assert admin_user.is_organisation_admin(organisation) is True

    # When
    admin_user.set_organisation_membership_active(organisation, is_active=False)

    # Then
    assert admin_user.is_organisation_admin(organisation) is False
    assert list(admin_user.get_admin_organisations()) == []


def test_get_active_organisations__deactivated_membership__is_excluded(
    organisation: Organisation, deactivated_staff_user: FFAdminUser
) -> None:
    # Given
    # A user whose membership of the organisation has been deactivated.

    # When
    active_organisations = deactivated_staff_user.get_active_organisations()

    # Then
    assert list(active_organisations) == []
    # The membership itself is retained.
    assert list(deactivated_staff_user.organisations.all()) == [organisation]


def test_list_organisations__deactivated_membership__is_excluded(
    staff_client: APIClient,
    organisation: Organisation,
    deactivated_staff_user: FFAdminUser,
) -> None:
    # Given
    # A user whose membership of their only organisation has been deactivated.

    # When
    response = staff_client.get(reverse("api-v1:organisations:organisation-list"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


def test_retrieve_organisation__deactivated_membership__returns_403(
    staff_client: APIClient,
    organisation: Organisation,
    deactivated_staff_user: FFAdminUser,
) -> None:
    # Given
    # A user whose membership of the organisation has been deactivated.

    # When
    response = staff_client.get(
        reverse("api-v1:organisations:organisation-detail", args=[organisation.id])
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_permitted_projects__deactivated_membership__returns_nothing(
    organisation: Organisation,
    project: Project,
    admin_user: FFAdminUser,
) -> None:
    # Given
    assert list(admin_user.get_permitted_projects("VIEW_PROJECT")) == [project]

    # When
    admin_user.set_organisation_membership_active(organisation, is_active=False)

    # Then
    assert list(admin_user.get_permitted_projects("VIEW_PROJECT")) == []


def test_has_organisation_permission__deactivated_membership__returns_false(
    organisation: Organisation,
    staff_user: FFAdminUser,
    with_organisation_permissions: WithOrganisationPermissionsCallable,
) -> None:
    # Given
    with_organisation_permissions(["CREATE_PROJECT"], None)
    assert staff_user.has_organisation_permission(organisation, "CREATE_PROJECT")

    # When
    staff_user.set_organisation_membership_active(organisation, is_active=False)

    # Then
    assert (
        staff_user.has_organisation_permission(organisation, "CREATE_PROJECT") is False
    )


def test_login__deactivated_membership__succeeds(
    api_client: APIClient,
    organisation: Organisation,
    deactivated_staff_user: FFAdminUser,
) -> None:
    # Given
    password = FFAdminUser.objects.make_random_password()
    deactivated_staff_user.set_password(password)  # type: ignore[no-untyped-call]
    deactivated_staff_user.save()

    # When
    response = api_client.post(
        reverse("api-v1:custom_auth:custom-mfa-authtoken-login"),
        data={"email": deactivated_staff_user.email, "password": password},
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["key"]


def test_add_organisation__new_membership__is_active(
    organisation: Organisation,
) -> None:
    # Given
    user = FFAdminUser.objects.create(email="new@example.com")

    # When
    user.add_organisation(organisation, role=OrganisationRole.USER)

    # Then
    assert user.belongs_to(organisation.id) is True
