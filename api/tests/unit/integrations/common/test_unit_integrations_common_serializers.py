from django.utils import timezone

from integrations.datadog.models import DataDogConfiguration
from integrations.datadog.serializers import DataDogConfigurationSerializer
from integrations.webhook.models import WebhookConfiguration
from integrations.webhook.serializers import WebhookConfigurationSerializer


def test_base_environment_integration_model_serializer_save_updates_existing_if_soft_deleted(
    environment,
):
    """
    To avoid creating a model only for testing, we use the WebhookConfigurationSerializer, which subclasses
    BaseEnvironmentIntegrationModelSerializer.
    """

    # Given
    old_url = "https://old.webhook.url/hook"
    new_url = "https://new.webhook.url/hook"

    serializer = WebhookConfigurationSerializer(data={"url": new_url})

    # create an existing webhookconfiguration object that has been soft deleted
    WebhookConfiguration.objects.create(
        environment=environment, url=old_url, deleted_at=timezone.now()
    )

    serializer.is_valid(raise_exception=True)

    # When
    serializer.save(environment=environment)

    # Then
    updated_webhook_config = WebhookConfiguration.objects.filter(
        environment=environment
    ).first()
    assert updated_webhook_config is not None
    assert updated_webhook_config.url == new_url
    assert updated_webhook_config.deleted_at is None


def test_base_project_integration_model_serializer_save_updates_existing_if_soft_deleted(
    project,
):
    """
    To avoid creating a model only for testing, we use the DataDogConfigurationSerializer, which subclasses
    BaseProjectIntegrationModelSerializer.
    """

    # Given
    old_url = "https://old.datadog.url"
    old_api_key = "some-old-key"

    new_url = "https://new.datadog.url"
    new_api_key = "some-new-key"

    serializer = DataDogConfigurationSerializer(
        data={"base_url": new_url, "api_key": new_api_key}
    )

    # create an existing webhookconfiguration object that has been soft deleted
    DataDogConfiguration.objects.create(
        project=project,
        base_url=old_url,
        api_key=old_api_key,
        deleted_at=timezone.now(),
    )

    serializer.is_valid(raise_exception=True)

    # When
    serializer.save(project_id=project.id)

    # Then
    updated_webhook_config = DataDogConfiguration.objects.filter(
        project=project
    ).first()
    assert updated_webhook_config is not None
    assert updated_webhook_config.base_url == new_url
    assert updated_webhook_config.api_key == new_api_key
    assert updated_webhook_config.deleted_at is None
