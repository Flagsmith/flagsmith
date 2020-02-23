from unittest import TestCase, mock

import pytest

from audit.models import AuditLog
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
class AuditLogTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test Organisation')
        self.project = Project.objects.create(name='Test project', organisation=self.organisation)

    @mock.patch('audit.signals.call_organisation_webhooks')
    def test_organisation_webhooks_are_called_when_audit_log_saved(self, mock_call_webhooks):
        # Given
        audit_log = AuditLog(project=self.project, log='Some audit log')

        # When
        audit_log.save()

        # Then
        mock_call_webhooks.assert_called()
