import pytest

from environments.identities.models import Identity


@pytest.fixture()
def identity_one(organisation_one_project_one_environment_one):
    return Identity.objects.create(
        identifier="identity_1",
        environment=organisation_one_project_one_environment_one,
    )
