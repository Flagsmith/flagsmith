from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.signals import call_webhooks
from organisations.models import Organisation
from projects.models import Project


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
    mocked_call_organisation_webhooks.assert_not_called()


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
    mocked_call_organisation_webhooks.assert_not_called()
