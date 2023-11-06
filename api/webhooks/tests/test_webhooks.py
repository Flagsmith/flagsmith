import hashlib
import hmac
import json
from typing import Type
from unittest import TestCase, mock

import pytest
from core.constants import FLAGSMITH_SIGNATURE_HEADER
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError, Timeout

from environments.models import Environment, Webhook
from organisations.models import Organisation, OrganisationWebhook
from projects.models import Project
from webhooks.sample_webhook_data import (
    environment_webhook_data,
    organisation_webhook_data,
)
from webhooks.webhooks import (
    WebhookEventType,
    WebhookType,
    call_environment_webhooks,
    call_organisation_webhooks,
    trigger_sample_webhook,
)


@pytest.mark.django_db
class WebhooksTestCase(TestCase):
    def setUp(self) -> None:
        organisation = Organisation.objects.create(name="Test organisation")
        project = Project.objects.create(name="Test project", organisation=organisation)
        self.environment = Environment.objects.create(
            name="Test environment", project=project
        )

    @mock.patch("webhooks.webhooks.requests")
    def test_requests_made_to_all_urls_for_environment(self, mock_requests):
        # Given
        webhook_1 = Webhook.objects.create(
            url="http://url.1.com", enabled=True, environment=self.environment
        )
        webhook_2 = Webhook.objects.create(
            url="http://url.2.com", enabled=True, environment=self.environment
        )

        # When
        call_environment_webhooks(
            environment_id=self.environment.id,
            data={},
            event_type=WebhookEventType.FLAG_UPDATED.value,
        )

        # Then
        assert len(mock_requests.post.call_args_list) == 2

        # and
        call_1_args, _ = mock_requests.post.call_args_list[0]
        call_2_args, _ = mock_requests.post.call_args_list[1]
        all_call_args = call_1_args + call_2_args
        assert all(
            str(webhook.url) in all_call_args for webhook in (webhook_1, webhook_2)
        )

    @mock.patch("webhooks.webhooks.requests")
    def test_request_not_made_to_disabled_webhook(self, mock_requests):
        # Given
        Webhook.objects.create(
            url="http://url.1.com", enabled=False, environment=self.environment
        )

        # When
        call_environment_webhooks(
            environment_id=self.environment.id,
            data={},
            event_type=WebhookEventType.FLAG_UPDATED.value,
        )

        # Then
        mock_requests.post.assert_not_called()

    @mock.patch("webhooks.webhooks.requests")
    def test_trigger_sample_webhook_makes_correct_post_request_for_environment(
        self, mock_request
    ):
        url = "http://test.test"
        webhook = Webhook(url=url)
        trigger_sample_webhook(webhook, WebhookType.ENVIRONMENT)
        args, kwargs = mock_request.post.call_args
        assert json.loads(kwargs["data"]) == environment_webhook_data
        assert args[0] == url

    @mock.patch("webhooks.webhooks.requests")
    def test_trigger_sample_webhook_makes_correct_post_request_for_organisation(
        self, mock_request
    ):
        url = "http://test.test"
        webhook = OrganisationWebhook(url=url)

        trigger_sample_webhook(webhook, WebhookType.ORGANISATION)
        args, kwargs = mock_request.post.call_args
        assert json.loads(kwargs["data"]) == organisation_webhook_data
        assert args[0] == url

    @mock.patch("webhooks.webhooks.WebhookSerializer")
    @mock.patch("webhooks.webhooks.requests")
    def test_request_made_with_correct_signature(
        self, mock_requests, webhook_serializer
    ):
        # Given
        payload = {"key": "value"}
        webhook_serializer.return_value.data = payload
        secret = "random_key"
        Webhook.objects.create(
            url="http://url.1.com",
            enabled=True,
            environment=self.environment,
            secret=secret,
        )

        expected_signature = hmac.new(
            key=secret.encode(),
            msg=json.dumps(payload).encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        call_environment_webhooks(
            environment_id=self.environment.id,
            data={},
            event_type=WebhookEventType.FLAG_UPDATED.value,
        )
        # When
        _, kwargs = mock_requests.post.call_args_list[0]
        # Then
        received_signature = kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]
        assert hmac.compare_digest(expected_signature, received_signature) is True

    @mock.patch("webhooks.webhooks.requests")
    def test_request_does_not_have_signature_header_if_secret_is_not_set(
        self, mock_requests
    ):
        # Given
        Webhook.objects.create(
            url="http://url.1.com", enabled=True, environment=self.environment
        )
        # When
        call_environment_webhooks(
            environment_id=self.environment.id,
            data={},
            event_type=WebhookEventType.FLAG_UPDATED.value,
        )

        # Then
        _, kwargs = mock_requests.post.call_args_list[0]
        assert FLAGSMITH_SIGNATURE_HEADER not in kwargs["headers"]


@pytest.mark.parametrize("expected_error", [ConnectionError, Timeout])
@pytest.mark.django_db
def test_call_environment_webhooks__multiple_webhooks__failure__calls_expected(
    mocker: MockerFixture,
    expected_error: Type[Exception],
    environment: Environment,
) -> None:
    # Given
    requests_post_mock = mocker.patch("webhooks.webhooks.requests.post")
    requests_post_mock.side_effect = expected_error()
    send_failure_email_mock: mock.Mock = mocker.patch(
        "webhooks.webhooks.send_failure_email"
    )

    webhook_1 = Webhook.objects.create(
        url="http://url.1.com",
        enabled=True,
        environment=environment,
    )
    webhook_2 = Webhook.objects.create(
        url="http://url.2.com",
        enabled=True,
        environment=environment,
    )

    expected_data = {}
    expected_event_type = WebhookEventType.FLAG_UPDATED.value
    expected_send_failure_email_data = {
        "event_type": expected_event_type,
        "data": expected_data,
    }
    expected_send_failure_status_code = f"N/A ({expected_error.__name__})"

    # When
    call_environment_webhooks(
        environment_id=environment.id,
        data=expected_data,
        event_type=expected_event_type,
    )

    # Then
    # Default is to retry 3 times for each webhook
    assert requests_post_mock.call_count == 2 * 3
    assert send_failure_email_mock.call_count == 2
    send_failure_email_mock.assert_has_calls(
        [
            mocker.call(
                webhook_2,
                expected_send_failure_email_data,
                WebhookType.ENVIRONMENT.value,
                expected_send_failure_status_code,
            ),
            mocker.call(
                webhook_1,
                expected_send_failure_email_data,
                WebhookType.ENVIRONMENT.value,
                expected_send_failure_status_code,
            ),
        ],
        any_order=True,
    )


@pytest.mark.parametrize("expected_error", [ConnectionError, Timeout])
@pytest.mark.django_db
def test_call_organisation_webhooks__multiple_webhooks__failure__calls_expected(
    mocker: MockerFixture, expected_error: Type[Exception], organisation: Organisation
) -> None:
    # Given
    requests_post_mock = mocker.patch("webhooks.webhooks.requests.post")
    requests_post_mock.side_effect = expected_error()
    send_failure_email_mock: mock.Mock = mocker.patch(
        "webhooks.webhooks.send_failure_email"
    )

    webhook_1 = OrganisationWebhook.objects.create(
        url="http://url.1.com", enabled=True, organisation=organisation
    )
    webhook_2 = OrganisationWebhook.objects.create(
        url="http://url.2.com", enabled=True, organisation=organisation
    )

    expected_data = {}
    expected_event_type = WebhookEventType.FLAG_UPDATED.value
    expected_send_failure_email_data = {
        "event_type": expected_event_type,
        "data": expected_data,
    }
    expected_send_failure_status_code = f"N/A ({expected_error.__name__})"

    # When
    call_organisation_webhooks(
        organisation_id=organisation.id,
        data=expected_data,
        event_type=expected_event_type,
    )

    # Then
    # Default is to retry 3 times for each webhook
    assert requests_post_mock.call_count == 2 * 3
    assert send_failure_email_mock.call_count == 2
    send_failure_email_mock.assert_has_calls(
        [
            mocker.call(
                webhook_2,
                expected_send_failure_email_data,
                WebhookType.ORGANISATION.value,
                expected_send_failure_status_code,
            ),
            mocker.call(
                webhook_1,
                expected_send_failure_email_data,
                WebhookType.ORGANISATION.value,
                expected_send_failure_status_code,
            ),
        ],
        any_order=True,
    )
