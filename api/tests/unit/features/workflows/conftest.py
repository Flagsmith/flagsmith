import pytest

from features.models import FeatureState
from features.workflows.models import ChangeRequest
from users.models import FFAdminUser


@pytest.fixture()
def change_request_no_required_approvals(environment, feature):
    user = FFAdminUser.objects.create(email="CR_creator@example.com")
    user.add_organisation(environment.project.organisation)
    from_feature_state = FeatureState.objects.get(
        environment=environment, feature=feature
    )
    to_feature_state = from_feature_state.create_new_version()
    to_feature_state.version = None
    to_feature_state.save()
    return ChangeRequest.objects.create(
        from_feature_state=from_feature_state,
        to_feature_state=to_feature_state,
        title="Change Request (no required approvals)",
        user=user,
    )
