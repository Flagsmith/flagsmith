import pytest

from features.models import FeatureState
from features.workflows.models import ChangeRequest
from users.models import FFAdminUser


@pytest.fixture()
def change_request_no_required_approvals(environment, feature):
    user = FFAdminUser.objects.create(email="CR_creator@example.com")
    user.add_organisation(environment.project.organisation)
    existing_feature_state = FeatureState.objects.get(
        environment=environment, feature=feature
    )

    change_request = ChangeRequest.objects.create(
        environment=environment,
        title="Change Request (no required approvals)",
        user=user,
    )

    new_feature_state = existing_feature_state.clone(env=environment, as_draft=True)
    new_feature_state.change_request = change_request
    new_feature_state.save()

    return change_request


@pytest.fixture()
def environment_with_1_required_cr_approval(environment):
    environment.minimum_change_request_approvals = 1
    environment.save()
    return environment
