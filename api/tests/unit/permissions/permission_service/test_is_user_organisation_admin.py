from collections.abc import Generator

import pytest
import structlog.contextvars
from common.core.request_context import get_request_context

from organisations.models import Organisation, OrganisationRole
from permissions.permission_service import is_user_organisation_admin
from users.models import FFAdminUser


@pytest.fixture(autouse=True)
def clear_request_context() -> Generator[None, None, None]:
    yield
    structlog.contextvars.clear_contextvars()


@pytest.mark.parametrize(
    "role, expected_is_admin",
    [(OrganisationRole.ADMIN, True), (OrganisationRole.USER, False)],
)
def test_is_user_organisation_admin__active_member__binds_organisation_id(
    staff_user: FFAdminUser,
    role: OrganisationRole,
    expected_is_admin: bool,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="Member Org")
    staff_user.add_organisation(organisation, role=role)

    # When
    is_admin = is_user_organisation_admin(staff_user, organisation)

    # Then
    assert is_admin is expected_is_admin
    assert get_request_context("organisation__id") == organisation.id


def test_is_user_organisation_admin__not_a_member__binds_nothing(
    staff_user: FFAdminUser,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="Other Org")

    # When
    is_admin = is_user_organisation_admin(staff_user, organisation)

    # Then
    assert is_admin is False
    assert get_request_context("organisation__id") is None
