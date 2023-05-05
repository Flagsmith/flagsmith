import pytest as pytest

from organisations.models import OrganisationRole
from organisations.permissions.models import UserOrganisationPermission
from organisations.permissions.permissions import VIEW_AUDIT_LOG
from permissions.models import PermissionModel


@pytest.fixture()
def view_audit_log_permission(db):
    return PermissionModel.objects.get(key=VIEW_AUDIT_LOG)


@pytest.fixture()
def view_audit_log_user(organisation, django_user_model, view_audit_log_permission):
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.USER)
    user_org_permission = UserOrganisationPermission.objects.create(
        user=user, organisation=organisation
    )
    user_org_permission.permissions.add(view_audit_log_permission)
    return user
