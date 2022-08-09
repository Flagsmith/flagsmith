from django.utils import timezone

from edge_api.identities.tasks import call_environment_webhook
from environments.models import Webhook
from webhooks.webhooks import WebhookEventType


def test_call_environment_webhook_with_new_state_only(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(environment=environment, url="https://foo.com/webhook")

    mock_feature_state_data = mocker.MagicMock()
    mock_generate_webhook_feature_state_data = mocker.patch.object(
        Webhook,
        "generate_webhook_feature_state_data",
        return_value=mock_feature_state_data,
    )

    now_isoformat = timezone.now().isoformat()
    new_enabled_state = True
    new_value = "foo"

    # When
    call_environment_webhook(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        new_enabled_state=new_enabled_state,
        new_value=new_value,
    )

    # Then
    mock_call_environment_webhooks.assert_called_once()
    call_args = mock_call_environment_webhooks.call_args

    assert call_args[0][0] == environment
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_UPDATED

    mock_generate_webhook_feature_state_data.assert_called_once_with(
        feature,
        environment,
        identity.id,
        identity.identifier,
        new_enabled_state,
        new_value,
    )
    data = call_args[0][1]
    assert data["new_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_with_previous_state_only(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(environment=environment, url="https://foo.com/webhook")

    mock_feature_state_data = mocker.MagicMock()
    mock_generate_webhook_feature_state_data = mocker.patch.object(
        Webhook,
        "generate_webhook_feature_state_data",
        return_value=mock_feature_state_data,
    )

    now_isoformat = timezone.now().isoformat()
    previous_enabled_state = True
    previous_value = "foo"

    # When
    call_environment_webhook(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        previous_enabled_state=previous_enabled_state,
        previous_value=previous_value,
    )

    # Then
    mock_call_environment_webhooks.assert_called_once()
    call_args = mock_call_environment_webhooks.call_args

    assert call_args[0][0] == environment
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_DELETED

    mock_generate_webhook_feature_state_data.assert_called_once_with(
        feature,
        environment,
        identity.id,
        identity.identifier,
        previous_enabled_state,
        previous_value,
    )
    data = call_args[0][1]
    assert data["previous_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_with_both_states(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(environment=environment, url="https://foo.com/webhook")

    mock_feature_state_data = mocker.MagicMock()
    mock_generate_webhook_feature_state_data = mocker.patch.object(
        Webhook,
        "generate_webhook_feature_state_data",
        return_value=mock_feature_state_data,
    )

    now_isoformat = timezone.now().isoformat()
    previous_enabled_state = False
    previous_value = "foo"

    new_enabled_state = True
    new_value = "bar"

    # When
    call_environment_webhook(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        previous_enabled_state=previous_enabled_state,
        previous_value=previous_value,
        new_enabled_state=new_enabled_state,
        new_value=new_value,
    )

    # Then
    mock_call_environment_webhooks.assert_called_once()
    call_args = mock_call_environment_webhooks.call_args

    assert call_args[0][0] == environment
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_UPDATED

    assert mock_generate_webhook_feature_state_data.call_count == 2
    mock_generate_data_calls = mock_generate_webhook_feature_state_data.call_args_list

    assert mock_generate_data_calls[0][0] == (
        feature,
        environment,
        identity.id,
        identity.identifier,
        previous_enabled_state,
        previous_value,
    )

    assert mock_generate_data_calls[1][0] == (
        feature,
        environment,
        identity.id,
        identity.identifier,
        new_enabled_state,
        new_value,
    )

    data = call_args[0][1]
    assert data["previous_state"] == mock_feature_state_data
    assert data["new_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat
