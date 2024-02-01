from copy import deepcopy

import pytest
from django.utils import timezone
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from edge_api.identities.tasks import (
    call_environment_webhook_for_feature_state_change,
    generate_audit_log_records,
    sync_identity_document_features,
    update_flagsmith_environments_v2_identity_overrides,
)
from environments.dynamodb.types import (
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.models import Environment, Webhook
from webhooks.webhooks import WebhookEventType


@pytest.mark.parametrize(
    "new_enabled_state, new_value",
    ((True, "foo"), (False, "foo"), (True, None), (False, None)),
)
def test_call_environment_webhook_for_feature_state_change_with_new_state_only(
    mocker, environment, feature, identity, admin_user, new_value, new_enabled_state
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

    assert call_args[0][0] == environment.id
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_UPDATED.value

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

    assert call_args[0][0] == environment.id
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_DELETED.value

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


@pytest.mark.parametrize(
    "previous_enabled_state, previous_value, new_enabled_state, new_value",
    (
        (True, None, True, "foo"),
        (True, "foo", False, "foo"),
        (True, "foo", True, "bar"),
        (True, None, False, None),
        (False, None, True, None),
    ),
)
def test_call_environment_webhook_for_feature_state_change_with_both_states(
    mocker,
    environment,
    feature,
    identity,
    admin_user,
    previous_enabled_state,
    previous_value,
    new_enabled_state,
    new_value,
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

    assert call_args[0][0] == environment.id
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_UPDATED.value

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
                        "old": {"enabled": False, "feature_state_value": None},
                        "new": {"enabled": True, "feature_state_value": None},
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
                        "new": {"enabled": True, "feature_state_value": None},
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
                        "old": {"enabled": True, "feature_state_value": None},
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


def test_update_flagsmith_environments_v2_identity_overrides__call_expected(
    mocker: MockerFixture,
    environment: Environment,
) -> None:
    # Given
    dynamodb_wrapper_v2_cls_mock = mocker.patch(
        "edge_api.identities.tasks.DynamoEnvironmentV2Wrapper"
    )
    dynamodb_wrapper_v2_mock = dynamodb_wrapper_v2_cls_mock.return_value
    identity_uuid = "a35a02f2-fefd-4932-8f5c-e84a0bf542c7"
    identifier = "identity1"
    changes = {
        "feature_overrides": {
            "test_feature": {
                "change_type": "~",
                "old": {
                    "enabled": False,
                    "feature_state_value": None,
                    "featurestate_uuid": "0729f130-8caa-4106-aa5c-95a6d15e820f",
                    "feature": {"id": 1, "name": "test_feature", "type": "STANDARD"},
                },
                "new": {
                    "enabled": True,
                    "feature_state_value": "updated",
                    "featurestate_uuid": "0729f130-8caa-4106-aa5c-95a6d15e820f",
                    "feature": {"id": 1, "name": "test_feature", "type": "STANDARD"},
                },
            },
            "test_feature2": {
                "change_type": "+",
                "new": {
                    "enabled": True,
                    "feature_state_value": "new",
                    "featurestate_uuid": "726c833a-5c9b-4c2c-954c-ddc46dd50bbb",
                    "feature": {"id": 2, "name": "test_feature2", "type": "STANDARD"},
                },
            },
            "test_feature3": {
                "change_type": "-",
                "old": {
                    "enabled": True,
                    "feature_state_value": "deleted",
                    "featurestate_uuid": "80f6dbdd-97c0-47de-9333-cd1e1c100713",
                    "feature": {"id": 3, "name": "test_feature3", "type": "STANDARD"},
                },
            },
        }
    }
    expected_identity_overrides_changeset = IdentityOverridesV2Changeset(
        to_delete=[
            IdentityOverrideV2.parse_obj(
                {
                    "document_key": f"identity_override:3:{identity_uuid}",
                    "environment_id": str(environment.id),
                    "environment_api_key": environment.api_key,
                    "identifier": identifier,
                    "identity_uuid": identity_uuid,
                    "feature_state": {
                        "enabled": True,
                        "feature_state_value": "deleted",
                        "featurestate_uuid": "80f6dbdd-97c0-47de-9333-cd1e1c100713",
                        "feature": {
                            "id": 3,
                            "name": "test_feature3",
                            "type": "STANDARD",
                        },
                    },
                }
            )
        ],
        to_put=[
            IdentityOverrideV2.parse_obj(
                {
                    "document_key": f"identity_override:1:{identity_uuid}",
                    "environment_id": str(environment.id),
                    "environment_api_key": environment.api_key,
                    "identifier": identifier,
                    "identity_uuid": identity_uuid,
                    "feature_state": {
                        "enabled": True,
                        "feature_state_value": "updated",
                        "featurestate_uuid": "0729f130-8caa-4106-aa5c-95a6d15e820f",
                        "feature": {
                            "id": 1,
                            "name": "test_feature",
                            "type": "STANDARD",
                        },
                    },
                }
            ),
            IdentityOverrideV2.parse_obj(
                {
                    "document_key": f"identity_override:2:{identity_uuid}",
                    "environment_id": str(environment.id),
                    "environment_api_key": environment.api_key,
                    "identifier": identifier,
                    "identity_uuid": identity_uuid,
                    "feature_state": {
                        "enabled": True,
                        "feature_state_value": "new",
                        "featurestate_uuid": "726c833a-5c9b-4c2c-954c-ddc46dd50bbb",
                        "feature": {
                            "id": 2,
                            "name": "test_feature2",
                            "type": "STANDARD",
                        },
                    },
                }
            ),
        ],
    )

    # When
    update_flagsmith_environments_v2_identity_overrides(
        environment_api_key=environment.api_key,
        identity_uuid=identity_uuid,
        changes=changes,
        identifier=identifier,
    )

    # Then
    dynamodb_wrapper_v2_mock.update_identity_overrides.assert_called_once_with(
        expected_identity_overrides_changeset,
    )


def test_update_flagsmith_environments_v2_identity_overrides__no_overrides__call_expected(
    mocker: MockerFixture,
    environment: Environment,
) -> None:
    # Given
    dynamodb_wrapper_v2_cls_mock = mocker.patch(
        "edge_api.identities.tasks.DynamoEnvironmentV2Wrapper"
    )
    dynamodb_wrapper_v2_mock = dynamodb_wrapper_v2_cls_mock.return_value
    identity_uuid = "a35a02f2-fefd-4932-8f5c-e84a0bf542c7"
    identifier = "identity1"
    changes = {"feature_overrides": []}

    # When
    update_flagsmith_environments_v2_identity_overrides(
        environment_api_key=environment.api_key,
        identity_uuid=identity_uuid,
        changes=changes,
        identifier=identifier,
    )

    # Then
    dynamodb_wrapper_v2_mock.update_identity_overrides.assert_not_called()
