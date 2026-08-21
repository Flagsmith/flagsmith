from datetime import timedelta
from io import StringIO

import freezegun
from django.core.management import call_command
from django.utils import timezone

from environments.models import Environment
from integrations.common.models import IntegrationHealthRecord
from integrations.common.services import record_integration_health
from integrations.webhook.models import WebhookConfiguration


def test_cleanup_integration_health_records__default_days__deletes_old_records_only(
    environment: Environment,
) -> None:
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )

    with freezegun.freeze_time(timezone.now() - timedelta(days=31)):
        record_integration_health(webhook_config, 200)

    record_integration_health(webhook_config, 200)

    stdout = StringIO()

    # When
    call_command("cleanup_integration_health_records", stdout=stdout)

    # Then
    assert IntegrationHealthRecord.objects.count() == 1
    assert (
        "Deleted 1 integration health record(s) older than 30 days."
        in stdout.getvalue()
    )


def test_cleanup_integration_health_records__custom_days__deletes_expected(
    environment: Environment,
) -> None:
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )

    with freezegun.freeze_time(timezone.now() - timedelta(days=10)):
        record_integration_health(webhook_config, 200)

    stdout = StringIO()

    # When
    call_command("cleanup_integration_health_records", days=5, stdout=stdout)

    # Then
    assert IntegrationHealthRecord.objects.count() == 0
    assert (
        "Deleted 1 integration health record(s) older than 5 days." in stdout.getvalue()
    )


def test_cleanup_integration_health_records__no_old_records__deletes_nothing(
    environment: Environment,
) -> None:
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )
    record_integration_health(webhook_config, 200)

    stdout = StringIO()

    # When
    call_command("cleanup_integration_health_records", stdout=stdout)

    # Then
    assert IntegrationHealthRecord.objects.count() == 1
    assert (
        "Deleted 0 integration health record(s) older than 30 days."
        in stdout.getvalue()
    )
