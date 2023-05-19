from pytest_mock.plugin import MockerFixture
from rest_framework.request import Request

from audit.permissions import OrganisationAuditLogPermissions
from audit.views import OrganisationAuditLogViewSet
from organisations.models import Organisation
from users.models import FFAdminUser


def test_organisation_audit_log_permission_has_permission_organisation_admin(
    organisation: Organisation, admin_user: FFAdminUser, mocker: MockerFixture
):
    # Given
    permissions = OrganisationAuditLogPermissions()

    request = mocker.MagicMock(spec=Request, user=admin_user)
    view = mocker.MagicMock(
        spec=OrganisationAuditLogViewSet, kwargs={"organisation_pk": organisation.id}
    )

    # When
    result = permissions.has_permission(request=request, view=view)

    # Then
    assert result is True


def test_organisation_audit_log_permission_has_permission_organisation_user_with_permission(
    organisation: Organisation, mocker: MockerFixture, view_audit_log_user: FFAdminUser
):
    # Given
    permissions = OrganisationAuditLogPermissions()

    request = mocker.MagicMock(spec=Request, user=view_audit_log_user)
    view = mocker.MagicMock(
        spec=OrganisationAuditLogViewSet, kwargs={"organisation_pk": organisation.id}
    )

    # When
    result = permissions.has_permission(request=request, view=view)

    # Then
    assert result is True


def test_organisation_audit_log_permission_has_permission_organisation_user_without_permission(
    organisation_one: Organisation,
    mocker: MockerFixture,
    organisation_one_user: FFAdminUser,
):
    # Given
    permissions = OrganisationAuditLogPermissions()

    request = mocker.MagicMock(spec=Request, user=organisation_one_user)
    view = mocker.MagicMock(
        spec=OrganisationAuditLogViewSet,
        kwargs={"organisation_pk": organisation_one.id},
    )

    # When
    result = permissions.has_permission(request=request, view=view)

    # Then
    assert result is False
