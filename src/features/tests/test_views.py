from unittest import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature, FeatureState
from organisations.models import Organisation
from projects.models import Project
from util.tests import Helper


class ProjectFeatureTestCase(TestCase):
    project_features_url = '/api/v1/projects/%s/features/'
    project_feature_detail_url = '/api/v1/projects/%s/features/%d/'
    post_template = '{ "name": "%s", "project": %d, "initial_value": "%s" }'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_create_feature_states_when_feature_created(self):
        # Given
        client = self.set_up()
        project = Project.objects.get(name="test project")
        environment_1 = Environment(name="env 1", project=project)
        environment_2 = Environment(name="env 2", project=project)
        environment_3 = Environment(name="env 3", project=project)
        environment_1.save()
        environment_2.save()
        environment_3.save()

        # When
        response = client.post(self.project_features_url % project.id,
                               data=self.post_template % ("test feature", project.id,
                                                          "This is a value"),
                               content_type='application/json')

        # Then
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        # check feature was created successfully
        self.assertEquals(1, Feature.objects.filter(name="test feature",
                                                    project=project.id).count())
        feature = Feature.objects.get(name="test feature", project=project.id)
        # check feature was added to all environments
        self.assertEquals(1, FeatureState.objects.filter(environment=environment_1,
                                                         feature=feature).count())
        self.assertEquals(1, FeatureState.objects.filter(environment=environment_2,
                                                         feature=feature).count())
        self.assertEquals(1, FeatureState.objects.filter(environment=environment_3,
                                                         feature=feature).count())

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.get(environment=environment_1, feature=feature)
        self.assertEquals("This is a value", feature_state.get_feature_state_value())

        Helper.clean_up()

    def test_should_delete_feature_states_when_feature_deleted(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        project = Project(name="test project", organisation=organisation)
        project.save()
        environment_1 = Environment(name="env 1", project=project)
        environment_2 = Environment(name="env 2", project=project)
        environment_3 = Environment(name="env 3", project=project)
        environment_1.save()
        environment_2.save()
        environment_3.save()
        client.post(self.project_features_url % project.id,
                    data=self.post_template % ("test feature", project.id, "This is a value"),
                    content_type='application/json')
        feature = Feature.objects.get(name="test feature", project=project.id)

        # When
        response = client.delete(self.project_feature_detail_url % (project.id, feature.id),
                                 data='{"id": %d}' % feature.id,
                                 content_type='application/json')

        # Then
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        # check feature was deleted succesfully
        self.assertEquals(0, Feature.objects.filter(name="test feature",
                                                    project=project.id).count())
        # check feature was removed from all environments
        self.assertEquals(0, FeatureState.objects.filter(environment=environment_1,
                                                         feature=feature).count())
        self.assertEquals(0, FeatureState.objects.filter(environment=environment_2,
                                                         feature=feature).count())
        self.assertEquals(0, FeatureState.objects.filter(environment=environment_3,
                                                         feature=feature).count())

        Helper.clean_up()