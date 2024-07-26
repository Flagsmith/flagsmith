from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.signals import call_webhooks, send_audit_log_event_to_grafana
from integrations.grafana.models import GrafanaProjectConfiguration
from organisations.models import Organisation, OrganisationWebhook
from projects.models import Project
from webhooks.webhooks import WebhookEventType


def test_call_webhooks_does_not_create_task_if_webhooks_disabled(
    organisation: Organisation,
    project: Project,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    audit_log = AuditLog(project=project)
    settings.DISABLE_WEBHOOKS = True

    mocked_call_organisation_webhooks = mocker.patch(
        "audit.signals.call_organisation_webhooks"
    )

    # When
    call_webhooks(sender=AuditLog, instance=audit_log)

    # Then
    mocked_call_organisation_webhooks.delay.assert_not_called()


def test_call_webhooks_does_not_create_task_if_organisation_has_no_webhooks(
    organisation: Organisation,
    project: Project,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    audit_log = AuditLog(project=project)
    settings.DISABLE_WEBHOOKS = False

    assert organisation.webhooks.count() == 0

    mocked_call_organisation_webhooks = mocker.patch(
        "audit.signals.call_organisation_webhooks"
    )

    # When
    call_webhooks(sender=AuditLog, instance=audit_log)

    # Then
    mocked_call_organisation_webhooks.delay.assert_not_called()


def test_call_webhooks_creates_task_if_organisation_has_webhooks(
    organisation: Organisation,
    project: Project,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    audit_log = AuditLog.objects.create(project=project)
    OrganisationWebhook.objects.create(
        organisation=organisation,
        name="Example webhook",
        url="http://example.com/webhook",
        enabled=True,
    )
    settings.DISABLE_WEBHOOKS = False

    mocked_call_organisation_webhooks = mocker.patch(
        "audit.signals.call_organisation_webhooks"
    )

    # When
    call_webhooks(sender=AuditLog, instance=audit_log)

    # Then
    mocked_call_organisation_webhooks.delay.assert_called_once()
    mock_call = mocked_call_organisation_webhooks.delay.call_args.kwargs
    assert mock_call["args"][0] == organisation.id
    assert mock_call["args"][1]["id"] == audit_log.id
    assert mock_call["args"][2] == WebhookEventType.AUDIT_LOG_CREATED.name


def test_send_audit_log_event_to_grafana__project_grafana_config__calls_expected(
    mocker: MockerFixture,
    project: Project,
) -> None:
    # Given
    grafana_config = GrafanaProjectConfiguration(base_url="test.com", api_key="test")
    project.grafana_config = grafana_config
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    grafana_wrapper_mock = mocker.patch("audit.signals.GrafanaWrapper", autospec=True)
    grafana_wrapper_instance_mock = grafana_wrapper_mock.return_value

    # When
    send_audit_log_event_to_grafana(AuditLog, audit_log_record)

    # Then
    grafana_wrapper_mock.assert_called_once_with(
        base_url=grafana_config.base_url,
        api_key=grafana_config.api_key,
    )
    grafana_wrapper_instance_mock.generate_event_data.assert_called_once_with(
        audit_log_record
    )
    grafana_wrapper_instance_mock.track_event_async.assert_called_once_with(
        event=grafana_wrapper_instance_mock.generate_event_data.return_value
    )
