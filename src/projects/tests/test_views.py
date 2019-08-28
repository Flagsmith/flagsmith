from unittest import TestCase

from rest_framework.test import APIClient

from organisations.models import Organisation
from projects.models import Project
from util.tests import Helper


class ProjectTestCase(TestCase):

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_create_a_project(self):
        client = self.set_up()

        # Given
        organisation = Organisation(name='ssg')
        organisation.save()
        project_name = 'project1'
        project_template = '{ "name" : "%s", "organisation" : "%s" }'
        # When
        client.post('/api/v1/projects/',
                    data=project_template % (project_name, organisation.id),
                    content_type='application/json')
        project = Project.objects.filter(name=project_name)
        # Then
        self.assertEquals(project.count(), 1)