from unittest import mock

import pytest

from environments.models import Environment
from features.models import Feature, FeatureState
from features.tasks import trigger_feature_state_change_webhooks
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
@mock.patch("features.tasks.Thread")
def test_trigger_feature_state_change_webhooks(MockThread):
    # Given
    initial_value = "initial"
    new_value = "new"

    organisation = Organisation.objects.create(name="Test organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    environment = Environment.objects.create(name="Test environment", project=project)
    feature = Feature.objects.create(
        name="Test feature", project=project, initial_value=initial_value
    )
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    MockThread.reset_mock()  # reset mock as it will have been called when setting up the data

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    call_list = MockThread.call_args_list

    environment_webhook_call_args = call_list[0]
    organisation_webhook_call_args = call_list[1]

    # verify that the data for both calls is the same
    assert (
        environment_webhook_call_args[1]["args"][1]
        == organisation_webhook_call_args[1]["args"][1]
    )

    data = environment_webhook_call_args[1]["args"][1]
    assert data["new_state"]["feature_state_value"] == new_value
    assert data["previous_state"]["feature_state_value"] == initial_value
