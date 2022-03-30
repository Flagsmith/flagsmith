import pytest

from features.models import FeatureState
from features.workflows.models import ChangeRequest
from users.models import FFAdminUser


@pytest.fixture()
def environment_with_0_required_cr_approvals(environment):
    environment.minimum_change_request_approvals = 0
    environment.save()
    return environment


@pytest.fixture()
def environment_with_1_required_cr_approval(environment):
    environment.minimum_change_request_approvals = 1
    environment.save()
    return environment


@pytest.fixture()
def change_request_no_required_approvals(
    environment_with_0_required_cr_approvals, feature
):
    user = FFAdminUser.objects.create(email="CR_creator@example.com")
    return _create_change_request(
        user, environment_with_0_required_cr_approvals, feature
    )


@pytest.fixture()
def change_request_1_required_approvals(
    environment_with_1_required_cr_approval, feature
):
    user = FFAdminUser.objects.create(email="CR_creator@example.com")
    return _create_change_request(
        user, environment_with_1_required_cr_approval, feature
    )


def _create_change_request(user, environment, feature):
    user.add_organisation(environment.project.organisation)
    existing_feature_state = FeatureState.objects.get(
        environment=environment, feature=feature
    )

    change_request = ChangeRequest.objects.create(
        environment=environment, title="Change Request", user=user
    )

    new_feature_state = existing_feature_state.clone(env=environment, as_draft=True)
    new_feature_state.change_request = change_request
    new_feature_state.save()

    return change_request
