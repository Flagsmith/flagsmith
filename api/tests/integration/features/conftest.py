import pytest
from rest_framework.test import APIClient

from environments.models import Environment
from features.versioning.tasks import enable_v2_versioning


@pytest.fixture()
def other_environment(
    admin_client: APIClient,
    project: int,
    versioned_environment: Environment,
) -> Environment:
    """A second environment in the project, versioned like the first one."""
    response = admin_client.post(
        "/api/v1/environments/",
        data={"name": "Other Environment", "project": project},
        format="json",
    )
    assert response.status_code == 201
    environment: Environment = Environment.objects.get(
        api_key=response.json()["api_key"]
    )
    if versioned_environment.use_v2_feature_versioning:
        enable_v2_versioning(environment_id=environment.id)
    return environment


@pytest.fixture(params=["feature_versioning_v1", "feature_versioning_v2"])
def versioned_environment(
    request: pytest.FixtureRequest,
    environment: int,
) -> Environment:
    if request.param == "feature_versioning_v2":
        enable_v2_versioning(environment_id=environment)
    return Environment.objects.get(id=environment)  # type: ignore[no-any-return]
