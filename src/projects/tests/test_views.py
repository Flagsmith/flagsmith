from unittest import TestCase

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
from projects.models import Project
from util.tests import Helper


@pytest.mark.django_db
class ProjectTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name="Test org")
        user.add_organisation(self.organisation)

    def test_should_create_a_project(self):
        # Given
        project_name = 'project1'
        project_template = '{ "name" : "%s", "organisation" : %d }'

        # When
        response = self.client.post('/api/v1/projects/',
                                    data=project_template % (project_name, self.organisation.id),
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.filter(name=project_name).count() == 1
