import typing
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from features.feature_health.models import FeatureHealthProvider
from features.feature_health.signals import feature_health_updated
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture
def feature_health_provider(
    project: Project,
    staff_user: FFAdminUser,
) -> FeatureHealthProvider:
    return FeatureHealthProvider.objects.create(  # type: ignore[no-any-return]
        created_by=staff_user,
        project=project,
        name="Webhook",
    )


@pytest.fixture
def feature_health_updated_receiver(
    mocker: MockerFixture,
) -> typing.Generator[MagicMock, None, None]:
    receiver = mocker.MagicMock(return_value=None)
    feature_health_updated.connect(receiver, weak=False)
    yield receiver
    feature_health_updated.disconnect(receiver)
