from unittest import TestCase, mock

import pytest

from audit.models import AuditLog, RelatedObjectType
from integrations.datadog.models import DataDogConfiguration
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
class AuditLogTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test Organisation")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )

    @mock.patch("audit.signals.call_organisation_webhooks")
    def test_organisation_webhooks_are_called_when_audit_log_saved(
        self, mock_call_webhooks
    ):
        # Given
        audit_log = AuditLog(project=self.project, log="Some audit log")

        # When
        audit_log.save()

        # Then
        mock_call_webhooks.assert_called()

    @mock.patch("integrations.datadog.datadog.DataDogWrapper.track_event_async")
    def test_data_dog_track_event_not_called_on_audit_log_saved_when_not_configured(
        self, datadog_mock
    ):
        # Given Audit log and project not configured for Datadog
        audit_log = AuditLog(project=self.project, log="Some audit log")

        # When Audit log saved
        audit_log.save()

        # Then datadog track even should not be triggered
        datadog_mock.track_event_async.assert_not_called()

    @mock.patch("integrations.datadog.datadog.DataDogWrapper.track_event_async")
    def test_data_dog_track_event_not_called_on_audit_log_saved_when_wrong(
        self, datadog_mock
    ):
        # Given Audit log and project configured for Datadog integration
        DataDogConfiguration.objects.create(
            project=self.project, base_url='http"//test.com', api_key="123key"
        )

        audit_log = AuditLog(project=self.project, log="Some audit log")
        audit_log2 = AuditLog(
            project=self.project,
            log="Some audit log",
            related_object_type=RelatedObjectType.ENVIRONMENT.name,
        )

        # When Audit log saved with wrong types
        audit_log.save()
        audit_log2.save()

        # Then datadog track even should not be triggered
        datadog_mock.track_event_async.assert_not_called()

    @mock.patch("integrations.datadog.datadog.DataDogWrapper.track_event_async")
    def test_data_dog_track_event_called_on_audit_log_saved_when_correct_type(
        self, datadog_mock
    ):
        # Given project configured for Datadog integration
        DataDogConfiguration.objects.create(
            project=self.project, base_url='http"//test.com', api_key="123key"
        )

        # When Audit logs created with correct type
        AuditLog.objects.create(
            project=self.project,
            log="Some audit log",
            related_object_type=RelatedObjectType.FEATURE.name,
        )
        AuditLog.objects.create(
            project=self.project,
            log="Some audit log",
            related_object_type=RelatedObjectType.FEATURE_STATE.name,
        )
        AuditLog.objects.create(
            project=self.project,
            log="Some audit log",
            related_object_type=RelatedObjectType.SEGMENT.name,
        )

        # Then datadog track even triggered for each AuditLog
        assert 3 == datadog_mock.call_count
