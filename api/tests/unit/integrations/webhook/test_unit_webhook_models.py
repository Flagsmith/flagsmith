from pytest_mock import MockerFixture

from environments.models import Environment
from integrations.webhook.models import WebhookConfiguration


def test_webhook_model__save__call_expected(
    environment: Environment, mocker: MockerFixture
) -> None:
    # Given
    environment_mock = mocker.patch("integrations.webhook.models.Environment")

    # When
    WebhookConfiguration.objects.create(environment=environment)

    # Then
    environment_mock.write_environment_documents.assert_called_with(
        environment_id=environment.id
    )
