from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from integrations.datadog.models import DataDogConfiguration


def test_organisation_webhooks_are_called_when_audit_log_saved(project, mocker):
    # Given
    mock_call_webhooks = mocker.patch("audit.signals.call_organisation_webhooks")

    audit_log = AuditLog(project=project, log="Some audit log")

    # When
    audit_log.save()

    # Then
    mock_call_webhooks.assert_called()


def test_data_dog_track_event_not_called_on_audit_log_saved_when_not_configured(
    project, mocker
):
    # Given Audit log and project not configured for Datadog
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )
    audit_log = AuditLog(project=project, log="Some audit log")

    # When Audit log saved
    audit_log.save()

    # Then datadog track even should not be triggered
    datadog_mock.track_event_async.assert_not_called()


def test_data_dog_track_event_not_called_on_audit_log_saved_when_wrong(mocker, project):
    # Given Audit log and project configured for Datadog integration
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )

    DataDogConfiguration.objects.create(
        project=project, base_url='http"//test.com', api_key="123key"
    )

    audit_log = AuditLog(project=project, log="Some audit log")
    audit_log2 = AuditLog(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.ENVIRONMENT.name,
    )

    # When Audit log saved with wrong types
    audit_log.save()
    audit_log2.save()

    # Then datadog track event should not be triggered
    datadog_mock.track_event_async.assert_not_called()


def test_data_dog_track_event_called_on_audit_log_saved_when_correct_type(
    project, mocker
):
    # Given project configured for Datadog integration
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )

    DataDogConfiguration.objects.create(
        project=project, base_url='http"//test.com', api_key="123key"
    )

    # When Audit logs created with correct type
    AuditLog.objects.create(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    AuditLog.objects.create(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
    )
    AuditLog.objects.create(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.SEGMENT.name,
    )

    # Then datadog track even triggered for each AuditLog
    assert 3 == datadog_mock.call_count
