import pytest

from features.feature_health.models import FeatureHealthProvider
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
        name="Sample",
    )
