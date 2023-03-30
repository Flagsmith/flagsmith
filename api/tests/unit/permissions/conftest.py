import pytest

from organisations.models import Organisation
from projects.models import Project


@pytest.fixture()
def other_organisation(db):
    org = Organisation.objects.create(name="Other Org")
    # admin_user.add_organisation(org, role=OrganisationRole.ADMIN)
    return org


@pytest.fixture()
def other_project(other_organisation):
    return Project.objects.create(name="Test Project", organisation=other_organisation)
