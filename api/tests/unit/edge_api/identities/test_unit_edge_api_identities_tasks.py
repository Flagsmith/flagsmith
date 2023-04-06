from copy import deepcopy

import pytest
from django.utils import timezone

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from edge_api.identities.tasks import (
    call_environment_webhook_for_feature_state_change,
    generate_audit_log_records,
    sync_identity_document_features,
)
from environments.models import Webhook
from webhooks.webhooks import WebhookEventType


def test_call_environment_webhook_for_feature_state_change_with_new_state_only(
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
    call_environment_webhook_for_feature_state_change(
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
        feature=feature,
        environment=environment,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        enabled=new_enabled_state,
        value=new_value,
    )
    data = call_args[0][1]
    assert data["new_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_for_feature_state_change_with_previous_state_only(
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
    call_environment_webhook_for_feature_state_change(
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
        feature=feature,
        environment=environment,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        enabled=previous_enabled_state,
        value=previous_value,
    )
    data = call_args[0][1]
    assert data["previous_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_for_feature_state_change_with_both_states(
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
    call_environment_webhook_for_feature_state_change(
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

    assert mock_generate_data_calls[0][1] == {
        "feature": feature,
        "environment": environment,
        "identity_id": identity.id,
        "identity_identifier": identity.identifier,
        "enabled": previous_enabled_state,
        "value": previous_value,
    }

    assert mock_generate_data_calls[1][1] == {
        "feature": feature,
        "environment": environment,
        "identity_id": identity.id,
        "identity_identifier": identity.identifier,
        "enabled": new_enabled_state,
        "value": new_value,
    }

    data = call_args[0][1]
    assert data["previous_state"] == mock_feature_state_data
    assert data["new_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_for_feature_state_change_does_nothing_if_no_webhooks(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(
        environment=environment, url="https://foo.com/webhook", enabled=False
    )
    now_isoformat = timezone.now().isoformat()

    # When
    call_environment_webhook_for_feature_state_change(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        new_enabled_state=True,
        new_value="foo",
    )

    # Then
    mock_call_environment_webhooks.assert_not_called()


def test_sync_identity_document_features_removes_deleted_features(
    edge_identity_dynamo_wrapper_mock,
    identity_document_without_fs,
    environment,
    feature,
):
    # Given
    identity_document = deepcopy(identity_document_without_fs)
    identity_uuid = identity_document["identity_uuid"]

    # let's add a feature to the identity that is not in the environment
    identity_document["identity_features"].append(
        {
            "feature_state_value": "feature_1_value",
            "featurestate_uuid": "4a8fbe06-d4cd-4686-a184-d924844bb422",
            "django_id": 1,
            "feature": {
                "name": "feature_that_does_not_exists",
                "type": "STANDARD",
                "id": 99,
            },
            "enabled": True,
        }
    )
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid.return_value = (
        identity_document_without_fs
    )

    # When
    sync_identity_document_features(identity_uuid)

    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        identity_uuid
    )
    edge_identity_dynamo_wrapper_mock.put_item.assert_called_with(
        identity_document_without_fs
    )


@pytest.mark.parametrize(
    "changes, identifier, expected_log_message",
    (
        (
            {
                "feature_overrides": {
                    "test_feature": {
                        "change_type": "~",
                        "old": {"enabled": False, "value": None},
                        "new": {"enabled": True, "value": None},
                    }
                }
            },
            "identifier",
            "Feature override updated for feature 'test_feature' and identity 'identifier'",
        ),
        (
            {
                "feature_overrides": {
                    "test_feature": {
                        "change_type": "+",
                        "new": {"enabled": True, "value": None},
                    }
                }
            },
            "identifier",
            "Feature override created for feature 'test_feature' and identity 'identifier'",
        ),
        (
            {
                "feature_overrides": {
                    "test_feature": {
                        "change_type": "-",
                        "old": {"enabled": True, "value": None},
                    }
                }
            },
            "identifier",
            "Feature override deleted for feature 'test_feature' and identity 'identifier'",
        ),
    ),
)
def test_generate_audit_log_records(
    changes, identifier, expected_log_message, db, environment, admin_user
):
    # Given
    identity_uuid = "a35a02f2-fefd-4932-8f5c-e84a0bf542c7"

    # When
    generate_audit_log_records(
        environment_api_key=environment.api_key,
        identifier=identifier,
        identity_uuid=identity_uuid,
        user_id=admin_user.id,
        changes=changes,
    )

    # Then
    assert AuditLog.objects.filter(
        log=expected_log_message,
        related_object_type=RelatedObjectType.EDGE_IDENTITY.name,
        related_object_uuid=identity_uuid,
        environment=environment,
    ).exists()
