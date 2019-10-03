import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from audit.models import RelatedObjectType, AuditLog
from environments.models import Identity, Environment, Trait, STRING
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment, SegmentRule, Condition, EQUAL

User = get_user_model()


class SegmentViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email='test@example.com')
        self.organisation = Organisation.objects.create(name='Test Organisation')
        self.user.add_organisation(self.organisation)
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
            'rules': [{
                'type': 'ALL',
                'rules': [],
                'conditions': []
            }]
        }

        # When
        res = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert res.status_code == status.HTTP_201_CREATED
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.SEGMENT.name).count() == 1

    def test_audit_log_created_when_segment_updated(self):
        # Given
        segment = Segment.objects.create(name='Test segment', project=self.project)
        url = reverse('api:v1:projects:project-segments-detail', args=[self.project.id, segment.id])
        data = {
            'name': 'New segment name',
            'project': self.project.id,
            'rules': [{
                'type': 'ALL',
                'rules': [],
                'conditions': []
            }]
        }

        # When
        res = self.client.put(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert res.status_code == status.HTTP_200_OK
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.SEGMENT.name).count() == 1

    def test_can_filter_by_identity_to_get_only_matching_segments(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'

        matching_segment = Segment.objects.create(name='Matching segment', project=self.project)
        matching_rule = SegmentRule.objects.create(segment=matching_segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=matching_rule, property=trait_key, operator=EQUAL, value=trait_value)

        Segment.objects.create(name='Non matching segment', project=self.project)

        environment = Environment.objects.create(name='Test environment', project=self.project)
        identity = Identity.objects.create(identifier='test-user', environment=environment)
        Trait.objects.create(identity=identity, trait_key=trait_key, value_type=STRING, string_value=trait_value)

        base_url = reverse('api:v1:projects:project-segments-list', args=[self.project.id])
        url = base_url + '?identity=%d' % identity.id

        # When
        res = self.client.get(url)

        # Then
        assert res.json().get('count') == 1

    def test_cannot_create_segments_without_rules(self):
        # Given
        url = reverse('api:v1:projects:project-segments-list', args=[self.project.id])
        data = {
            'name': 'New segment name',
            'project': self.project.id,
            'rules': []
        }

        # When
        res = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST
