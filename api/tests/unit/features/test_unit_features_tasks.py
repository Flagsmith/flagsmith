import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from features.models import Feature, FeatureState
from features.tasks import trigger_feature_state_change_webhooks
from organisations.models import Organisation
from projects.models import Project
from webhooks.webhooks import WebhookEventType


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks(mocker: MockerFixture):
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

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    assert environment_webhook_call_args[0] == environment.id
    assert organisation_webhook_call_args[0] == organisation.id

    # verify that the data for both calls is the same
    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"]["feature_state_value"] == new_value
    assert data["previous_state"]["feature_state_value"] == initial_value
    assert event_type == WebhookEventType.FLAG_UPDATED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks_for_deleted_flag(
    mocker, organisation, project, environment, feature
):
    # Given
    new_value = "new"
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    trigger_feature_state_change_webhooks(feature_state, WebhookEventType.FLAG_DELETED)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    # verify that the data for both calls is the same
    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"] is None
    assert data["previous_state"]["feature_state_value"] == new_value
    assert event_type == WebhookEventType.FLAG_DELETED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks_for_deleted_flag_uses_fs_instance(
    mocker: MockerFixture,
    environment: Environment,
    feature: Feature,
):
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # Remove history instance to make sure it's not used
    feature_state.history.all().delete()

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    trigger_feature_state_change_webhooks(feature_state, WebhookEventType.FLAG_DELETED)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    # verify that the data for both calls is the same
    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"] is None

    assert data["previous_state"]["feature"]["id"] == feature_state.feature.id
    assert event_type == WebhookEventType.FLAG_DELETED.value
