import pytest

from features.models import FeatureState
from features.workflows.core.models import ChangeRequest
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


@pytest.fixture()
def mock_plaintext_content():
    return "plaintext content"


@pytest.fixture()
def mock_html_content():
    return "<p>html content</p>"


@pytest.fixture()
def mock_render_to_string(mocker, mock_plaintext_content, mock_html_content):
    _mock_render_to_string = mocker.MagicMock()

    def render_to_string_side_effect(template_name: str, context: dict):
        if template_name.endswith("html"):
            return mock_html_content
        elif template_name.endswith(".txt"):
            return mock_plaintext_content
        raise ValueError("Unknown template provided!")

    _mock_render_to_string.side_effect = render_to_string_side_effect
    return _mock_render_to_string
