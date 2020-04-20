from unittest import TestCase, mock

import pytest

from environments.models import Environment, Webhook
from organisations.models import Organisation
from projects.models import Project
from webhooks.webhooks import call_environment_webhooks, WebhookEventType


@pytest.mark.django_db
class WebhooksTestCase(TestCase):
    def setUp(self) -> None:
        organisation = Organisation.objects.create(name='Test organisation')
        project = Project.objects.create(name='Test project', organisation=organisation)
        self.environment = Environment.objects.create(name='Test environment', project=project)

    @mock.patch('webhooks.webhooks.requests')
    def test_requests_made_to_all_urls_for_environment(self, mock_requests):
        # Given
        webhook_1 = Webhook.objects.create(url='http://url.1.com', enabled=True, environment=self.environment)
        webhook_2 = Webhook.objects.create(url='http://url.2.com', enabled=True, environment=self.environment)

        # When
        call_environment_webhooks(environment=self.environment, data={}, event_type=WebhookEventType.FLAG_UPDATED)

        # Then
        assert len(mock_requests.post.call_args_list) == 2

        # and
        call_1_args, _ = mock_requests.post.call_args_list[0]
        call_2_args, _ = mock_requests.post.call_args_list[1]
        all_call_args = call_1_args + call_2_args
        assert all(str(webhook.url) in all_call_args for webhook in (webhook_1, webhook_2))

    @mock.patch('webhooks.webhooks.requests')
    def test_request_not_made_to_disabled_webhook(self, mock_requests):
        # Given
        Webhook.objects.create(url='http://url.1.com', enabled=False, environment=self.environment)

        # When
        call_environment_webhooks(environment=self.environment, data={}, event_type=WebhookEventType.FLAG_UPDATED)

        # Then
        mock_requests.post.assert_not_called()
