import json

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from environments.models import Environment, Identity
from features.models import Feature, FeatureState
from projects.models import Project
from organisations.models import Organisation

from rest_framework import status

from users.models import FFAdminUser, Invite


class OrganisationTestCase(TestCase):
    put_template = '{ "name" : "%s"}'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_return_organisation_list_when_requested(self):
        # Given
        client = self.set_up()

        # When
        response = client.get('/api/v1/organisations/')

        # Then
        self.assertEquals(response.status_code, 200)
        self.assertTrue('count' in response.data and response.data['count'] == 1)

    def test_should_update_organisation_name(self):
        client = self.set_up()

        # Given
        organisation = Organisation.objects.get(name="test org")
        # When
        ssg = 'ssg'
        response = client.put('/api/v1/organisations/%s/' % organisation.id,
                              data=self.put_template % ssg,
                              content_type='application/json')
        # Then
        organisation.refresh_from_db()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(organisation.name, ssg)

    def test_should_invite_users(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")

        # When
        response = client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                               data='{"emails":["test@example.com"], '
                                    '"frontend_base_url": "https://example.com"}',
                               content_type='application/json')

        # Then
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        invite = Invite.objects.get(email="test@example.com")
        # check hash was created
        self.assertTrue(invite.hash)

    def test_should_fail_if_invite_exists_already(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        email = "test_2@example.com"
        data = '{"emails":["%s"], "frontend_base_url": "https://example.com"}' % email

        # When
        response_success = client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                       data=data,
                                       content_type='application/json')
        response_fail = client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                    data=data,
                                    content_type='application/json')

        #Then
        self.assertEquals(response_success.status_code, status.HTTP_201_CREATED)
        self.assertEquals(response_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("error" in json.loads(response_fail.content))

        invites = Invite.objects.filter(email=email, organisation=organisation)
        self.assertEquals(len(invites), 1)

    def test_should_return_all_invites_and_can_resend(self):
        # Given
        client = self.set_up()
        organisation_2 = Organisation.objects.create(name="Test org 2")
        invite_1 = Invite.objects.create(email="test_1@example.com",
                                         frontend_base_url="https://www.example.com",
                                         organisation=organisation_2)
        invite_2 = Invite.objects.create(email="test_2@example.com",
                                         frontend_base_url="https://www.example.com",
                                         organisation=organisation_2)

        # When
        invite_list_response = client.get('/api/v1/organisations/%s/invites/' % organisation_2.id)
        invite_resend_response = client.post('/api/v1/organisations/%s/invites/%s/resend/' % (
            organisation_2.id, invite_1.id))

        # Then
        self.assertEquals(invite_list_response.status_code, status.HTTP_200_OK)
        self.assertEquals(invite_resend_response.status_code, status.HTTP_200_OK)


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


class EnvironmentTestCase(TestCase):
    fs_put_template = '{ "id" : %d, "enabled" : "%r", "feature_state_value" : "%s" }'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_return_identities_for_an_environment(self):
        client = self.set_up()

        # Given
        identifierOne = 'user1'
        identifierTwo = 'user2'
        organisation = Organisation(name='ssg')
        organisation.save()
        project = Project(name='project1', organisation=organisation)
        project.save()
        environment = Environment(name='environment1', project=project)
        environment.save()
        identityOne = Identity(identifier=identifierOne, environment=environment)
        identityOne.save()
        identityTwo = Identity(identifier=identifierTwo, environment=environment)
        identityTwo.save()
        # When
        response = client.get('/api/v1/environments/%s/identities/' % environment.api_key)
        # Then
        self.assertEquals(response.data['results'][0]['identifier'], identifierOne)
        self.assertEquals(response.data['results'][1]['identifier'], identifierTwo)

    def test_should_update_value_of_feature_state(self):
        # Given
        client = self.set_up()
        project = Project.objects.get(name="test project")
        feature = Feature(name="feature", project=project)
        feature.save()
        environment = Environment.objects.get(name="test env")
        feature_state = FeatureState.objects.get(feature=feature, environment=environment)

        # When
        response = client.put("/api/v1/environments/%s/featurestates/%d/" %
                              (environment.api_key, feature_state.id),
                              data=self.fs_put_template % (feature_state.id,
                                                           True,
                                                           "This is a value"),
                              content_type='application/json')  # should change enabled to True

        # Then
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        feature_state.refresh_from_db()
        self.assertEquals(feature_state.get_feature_state_value(), "This is a value")
        self.assertEquals(feature_state.enabled, True)

        Helper.clean_up()


class IdentityTestCase(TestCase):
    identifier = 'user1'
    put_template = '{ "enabled" : "%r" }'
    post_template = '{ "feature" : "%s", "enabled" : "%r" }'
    feature_states_url = '/api/v1/environments/%s/identities/%s/featurestates/'
    feature_states_detail_url = feature_states_url + "%d/"
    identities_url = '/api/v1/environments/%s/identities/%s/'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_return_identities_list_when_requested(self):
        # Given
        client = self.set_up()
        identity, project = Helper.generate_database_models(identifier=self.identifier)
        # When
        response = client.get(self.identities_url % (identity.environment.api_key,
                                                     identity.identifier))
        # Then
        self.assertEquals(response.status_code, 200)
        Helper.clean_up()

    def test_should_create_identityFeature_when_post(self):
        # Given
        client = self.set_up()
        environment = Environment.objects.get(name="test env")
        identity = Identity.objects.create(environment=environment, identifier="testidentity")
        project = Project.objects.get(name="test project")
        feature = Feature(name='feature1', project=project)
        feature.save()
        # When
        response = client.post(self.feature_states_url % (identity.environment.api_key,
                                                          identity.identifier),
                               data=self.post_template % (feature.id, True),
                               content_type='application/json')
        # Then
        identityFeature = identity.identity_features
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(identityFeature.count(), 1)
        Helper.clean_up()

    def test_should_return_BadRequest_when_duplicate_identityFeature_is_posted(self):
        # Given
        client = self.set_up()
        identity, project = Helper.generate_database_models(self.identifier)
        feature = Feature(name='feature2', project=project)
        feature.save()
        # When
        initialResponse = client.post(self.feature_states_url % (identity.environment.api_key,
                                                                 identity.identifier),
                                      data=self.post_template % (feature.id, True),
                                      content_type='application/json')
        secondResponse = client.post(self.feature_states_url % (identity.environment.api_key,
                                                                identity.identifier),
                                     data=self.post_template % (feature.id, True),
                                     content_type='application/json')
        # Then
        identityFeature = identity.identity_features
        self.assertEquals(initialResponse.status_code, status.HTTP_201_CREATED)
        self.assertEquals(secondResponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(identityFeature.count(), 1)
        Helper.clean_up()

    def test_should_change_enabled_state_when_put(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        project = Project.objects.get(name="test project", organisation=organisation)
        feature = Feature(name='feature1', project=project)
        feature.save()
        environment = Environment.objects.get(name="test env")
        identity = Identity(identifier="test_identity", environment=environment)
        identity.save()
        feature_state = FeatureState(feature=feature,
                                     identity=identity,
                                     enabled=False,
                                     environment=environment)
        feature_state.save()
        # When
        response = client.put(self.feature_states_detail_url % (identity.environment.api_key,
                                                                identity.identifier,
                                                                feature_state.id),
                              data=self.put_template % True,
                              content_type='application/json')
        feature_state.refresh_from_db()
        # Then
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(feature_state.enabled, True)
        Helper.clean_up()

    def test_should_remove_identityfeature_when_delete(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        project = Project.objects.get(name="test project", organisation=organisation)
        feature_one = Feature(name='feature1', project=project)
        feature_one.save()
        feature_two = Feature(name='feature2', project=project)
        feature_two.save()
        environment = Environment.objects.get(name="test env")
        identity = Identity(identifier="test_identity", environment=environment)
        identity.save()
        environment = Environment.objects.get(name="test env")
        identity_feature_one = FeatureState(feature=feature_one,
                                            identity=identity,
                                            enabled=False,
                                            environment=environment)
        identity_feature_one.save()
        identity_feature_two = FeatureState(feature=feature_two,
                                            identity=identity,
                                            enabled=True,
                                            environment=environment)
        identity_feature_two.save()
        # When
        client.delete(self.feature_states_detail_url % (identity.environment.api_key,
                                                        identity.identifier,
                                                        identity_feature_one.id),
                      content_type='application/json')
        # Then
        identity_features = FeatureState.objects.filter(identity=identity)
        self.assertEquals(identity_features.count(), 1)
        Helper.clean_up()


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


class UserTestCase(TestCase):
    auth_base_url = '/api/v1/auth/'
    register_template = '{ ' \
                        '"email": "%s", ' \
                        '"first_name": "%s", ' \
                        '"last_name": "%s", ' \
                        '"password1": "%s", ' \
                        '"password2": "%s" ' \
                        '}'
    login_template = '{' \
                     '"email": "%s",' \
                     '"password": "%s"' \
                     '}'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_registration_and_login(self):
        Helper.generate_database_models()
        # When
        register_response = self.client.post(self.auth_base_url + "register/",
                                             data=self.register_template % ("johndoe@example.com",
                                                                            "john",
                                                                            "doe",
                                                                            "johndoe123",
                                                                            "johndoe123"),
                                             content_type='application/json')

        # Then
        self.assertEquals(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("key", register_response.data)
        # Check user was created
        self.assertEquals(FFAdminUser.objects.filter(email="johndoe@example.com").count(), 1)
        user = FFAdminUser.objects.get(email="johndoe@example.com")
        organisation = Organisation(name="test org")
        organisation.save()
        user.organisation = organisation
        user.save()
        # Check user can login
        login_response = self.client.post(self.auth_base_url + "login/",
                                          data=self.login_template % (
                                              "johndoe@example.com", "johndoe123"),
                                          content_type='application/json')
        self.assertEquals(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("key", login_response.data)

        # verify key works on authenticated endpoint
        content = login_response.data
        organisations_response = self.client.get("/api/v1/organisations/",
                                                 HTTP_AUTHORIZATION="Token " + content['key'])
        self.assertEquals(organisations_response.status_code, status.HTTP_200_OK)

        Helper.clean_up()

    def test_join_organisation(self):
        # Given
        client = self.set_up()
        organisation_2 = Organisation(name="test org 2")
        organisation_2.save()
        invite = Invite(email="test_user@test.com", organisation=organisation_2)
        invite.save()
        user = FFAdminUser.objects.get(email="test_user@test.com")
        token = Token(user=user)
        token.save()

        # When
        response = client.post("/api/v1/users/join/" + invite.hash + "/",
                               HTTP_AUTHORIZATION="Token " + token.key)
        user.refresh_from_db()

        # Then
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(user.organisations.all().count(), 2)


class Helper:
    def __init__(self):
        pass

    @staticmethod
    def generate_database_models(identifier='user1'):
        organisation = Organisation(name='ssg')
        organisation.save()
        project = Project(name='project1', organisation=organisation)
        project.save()
        environment = Environment(name='environment1', project=project)
        environment.save()
        feature = Feature(name="feature1", project=project)
        feature.save()
        identity = Identity(identifier=identifier, environment=environment)
        identity.save()
        return identity, project

    @staticmethod
    def clean_up():
        Identity.objects.all().delete()
        FeatureState.objects.all().delete()
        Feature.objects.all().delete()
        Environment.objects.all().delete()
        Project.objects.all().delete()
        Organisation.objects.all().delete()

    @staticmethod
    def create_ffadminuser():
        Helper.clean_up()
        organisation = Organisation(name='test org')
        organisation.save()
        project = Project(name="test project", organisation=organisation)
        project.save()
        environment = Environment(name="test env", project=project)
        environment.save()
        user = FFAdminUser(username="test_user", email="test_user@test.com",
                           first_name="test", last_name="user")
        user.set_password("testuser123")
        user.save()
        user.organisations.add(organisation)
        user.save()
        return user
