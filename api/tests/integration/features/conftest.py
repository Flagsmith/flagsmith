from datetime import datetime

import pytest
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import enable_v2_versioning
from features.workflows.core.models import ChangeRequest
from tests.types import CreateChangeRequestSegmentOverrideFixture
from users.models import FFAdminUser


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


@pytest.fixture()
def create_change_request_segment_override(
    admin_user: FFAdminUser,
) -> CreateChangeRequestSegmentOverrideFixture:
    """Return a callable putting a segment override through a change request, whichever versioning is in use."""

    def _create_change_request_segment_override(
        environment: Environment,
        feature_id: int,
        segment_id: int,
        committed: bool = False,
        live_from: datetime | None = None,
    ) -> None:
        change_request = ChangeRequest.objects.create(
            environment=environment, title="Pending", user=admin_user
        )
        version = (
            EnvironmentFeatureVersion.objects.create(
                environment=environment,
                feature_id=feature_id,
                change_request=change_request,
                live_from=live_from,
            )
            if environment.use_v2_feature_versioning
            else None
        )
        feature_segment = FeatureSegment.objects.create(
            environment=environment,
            feature_id=feature_id,
            segment_id=segment_id,
            environment_feature_version=version,
        )
        FeatureState.objects.create(
            environment=environment,
            feature_id=feature_id,
            feature_segment=feature_segment,
            environment_feature_version=version,
            change_request=None if version else change_request,
            live_from=live_from,
            enabled=True,
        )
        if committed:
            change_request.commit(committed_by=admin_user)

    return _create_change_request_segment_override
