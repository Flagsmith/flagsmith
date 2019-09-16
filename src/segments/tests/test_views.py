import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from audit.models import RelatedObjectType, AuditLog
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment

User = get_user_model()


class SegmentViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email='test@example.com')
        self.organisation = Organisation.objects.create(name='Test Organisation')
        self.user.organisations.add(self.organisation)
        self.client.force_authenticate(self.user)
        self.project = Project.objects.create(name='Test project', organisation=self.organisation)

    def tearDown(self) -> None:
        AuditLog.objects.all().delete()

    def test_audit_log_created_when_segment_created(self):
        # Given
        url = reverse('api:v1:projects:project-segments-list', args=[self.project.id])
        data = {
            'name': 'Test Segment',
            'project': self.project.id,
            'rules': []
        }

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.SEGMENT.name).count() == 1

    def test_audit_log_created_when_segment_updated(self):
        # Given
        segment = Segment.objects.create(name='Test segment', project=self.project)
        url = reverse('api:v1:projects:project-segments-detail', args=[self.project.id, segment.id])
        data = {
            'name': 'New segment name',
            'project': self.project.id,
            'rules': []
        }

        # When
        self.client.put(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.SEGMENT.name).count() == 1
