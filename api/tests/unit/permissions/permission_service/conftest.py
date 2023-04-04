import pytest

from organisations.roles.models import (
    RoleEnvironmentPermission,
    RoleOrganisationPermission,
)


@pytest.fixture
def role_environment_permission(role, environment):
    return RoleEnvironmentPermission.objects.create(role=role, environment=environment)


@pytest.fixture
def role_organisation_permission(role, organisation):
    return RoleOrganisationPermission.objects.create(role=role)
