import json
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from audit.models import AuditLog, RelatedObjectType
from environments.models import Environment, Trait, INTEGER, STRING, Webhook
from environments.identities.models import Identity
from environments.permissions.models import UserEnvironmentPermission
from features.models import Feature, FeatureState
from organisations.models import Organisation, OrganisationRole
from projects.models import Project, UserProjectPermission, ProjectPermissionModel
from users.models import FFAdminUser
from util.tests import Helper


@pytest.mark.django_db
class EnvironmentTestCase(TestCase):
    env_post_template = '{"name": "%s", "project": %d}'
    fs_put_template = '{ "id" : %d, "enabled" : "%r", "feature_state_value" : "%s" }'

    def setUp(self):
        self.client = APIClient()
        self.user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=self.user)

        create_environment_permission = ProjectPermissionModel.objects.get(key="CREATE_ENVIRONMENT")
        read_project_permission = ProjectPermissionModel.objects.get(key="VIEW_PROJECT")

        self.organisation = Organisation.objects.create(name='ssg')
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)  # admin to bypass perms

        self.project = Project.objects.create(name='Test project', organisation=self.organisation)

        user_project_permission = UserProjectPermission.objects.create(user=self.user, project=self.project)
        user_project_permission.permissions.add(create_environment_permission, read_project_permission)

    def tearDown(self) -> None:
        Environment.objects.all().delete()
        AuditLog.objects.all().delete()

    def test_should_create_environments(self):
        # Given
        url = reverse('api-v1:environments:environment-list')
        data = {
            'name': 'Test environment',
            'project': self.project.id
        }

        # When
        response = self.client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        # and user is admin
        assert UserEnvironmentPermission.objects.filter(user=self.user, admin=True,
                                                        environment__id=response.json()['id']).exists()

    def test_should_return_identities_for_an_environment(self):
        # Given
        identifier_one = 'user1'
        identifier_two = 'user2'
        environment = Environment.objects.create(name='environment1', project=self.project)
        Identity.objects.create(identifier=identifier_one, environment=environment)
        Identity.objects.create(identifier=identifier_two, environment=environment)
        url = reverse('api-v1:environments:environment-identities-list', args=[environment.api_key])

        # When
        response = self.client.get(url)

        # Then
        assert response.data['results'][0]['identifier'] == identifier_one
        assert response.data['results'][1]['identifier'] == identifier_two

    def test_should_update_value_of_feature_state(self):
        # Given
        feature = Feature.objects.create(name="feature", project=self.project)
        environment = Environment.objects.create(name="test env", project=self.project)
        feature_state = FeatureState.objects.get(feature=feature, environment=environment)
        url = reverse('api-v1:environments:environment-featurestates-detail',
                      args=[environment.api_key, feature_state.id])

        # When
        response = self.client.put(url, data=self.fs_put_template % (feature_state.id, True, "This is a value"),
                                   content_type='application/json')

        # Then
        feature_state.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert feature_state.get_feature_state_value() == "This is a value"
        assert feature_state.enabled

    def test_audit_log_entry_created_when_new_environment_created(self):
        # Given
        url = reverse('api-v1:environments:environment-list')
        data = {
            'project': self.project.id,
            'name': 'Test Environment'
        }

        # When
        self.client.post(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.ENVIRONMENT.name).count() == 1

    def test_audit_log_entry_created_when_environment_updated(self):
        # Given
        environment = Environment.objects.create(name='Test environment', project=self.project)
        url = reverse('api-v1:environments:environment-detail', args=[environment.api_key])
        data = {
            'project': self.project.id,
            'name': 'New name'
        }

        # When
        self.client.put(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.ENVIRONMENT.name).count() == 1

    def test_audit_log_created_when_feature_state_updated(self):
        # Given
        feature = Feature.objects.create(name="feature", project=self.project)
        environment = Environment.objects.create(name="test env", project=self.project)
        feature_state = FeatureState.objects.get(feature=feature, environment=environment)
        url = reverse('api-v1:environments:environment-featurestates-detail',
                      args=[environment.api_key, feature_state.id])
        data = {
            'id': feature.id,
            'enabled': True
        }

        # When
        self.client.put(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE_STATE.name).count() == 1

        # and
        assert AuditLog.objects.first().author

    def test_get_all_trait_keys_for_environment_only_returns_distinct_keys(self):
        # Given
        trait_key_one = 'trait-key-one'
        trait_key_two = 'trait-key-two'

        environment = Environment.objects.create(project=self.project, name='Test Environment')

        identity_one = Identity.objects.create(environment=environment, identifier='identity-one')
        identity_two = Identity.objects.create(environment=environment, identifier='identity-two')

        Trait.objects.create(identity=identity_one, trait_key=trait_key_one, string_value='blah', value_type=STRING)
        Trait.objects.create(identity=identity_one, trait_key=trait_key_two, string_value='blah', value_type=STRING)
        Trait.objects.create(identity=identity_two, trait_key=trait_key_one, string_value='blah', value_type=STRING)

        url = reverse('api-v1:environments:environment-trait-keys', args=[environment.api_key])

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and - only distinct keys are returned
        assert len(res.json().get('keys')) == 2

    def test_delete_trait_keys_deletes_trait_for_all_users_in_that_environment(self):
        # Given
        environment_one = Environment.objects.create(project=self.project, name='Test Environment 1')
        environment_two = Environment.objects.create(project=self.project, name='Test Environment 2')

        identity_one_environment_one = Identity.objects.create(environment=environment_one,
                                                               identifier='identity-one-env-one')
        identity_one_environment_two = Identity.objects.create(environment=environment_two,
                                                               identifier='identity-one-env-two')

        trait_key = 'trait-key'
        Trait.objects.create(identity=identity_one_environment_one, trait_key=trait_key, string_value='blah',
                             value_type=STRING)
        Trait.objects.create(identity=identity_one_environment_two, trait_key=trait_key, string_value='blah',
                             value_type=STRING)

        url = reverse('api-v1:environments:environment-delete-traits', args=[environment_one.api_key])

        # When
        self.client.post(url, data={'key': trait_key})

        # Then
        assert not Trait.objects.filter(identity=identity_one_environment_one, trait_key=trait_key).exists()

        # and
        assert Trait.objects.filter(identity=identity_one_environment_two, trait_key=trait_key).exists()

    def test_delete_trait_keys_deletes_traits_matching_provided_key_only(self):
        # Given
        environment = Environment.objects.create(project=self.project, name='Test Environment')

        identity = Identity.objects.create(identifier='test-identity', environment=environment)

        trait_to_delete = 'trait-key-to-delete'
        Trait.objects.create(identity=identity, trait_key=trait_to_delete, value_type=STRING, string_value='blah')

        trait_to_persist = 'trait-key-to-persist'
        Trait.objects.create(identity=identity, trait_key=trait_to_persist, value_type=STRING, string_value='blah')

        url = reverse('api-v1:environments:environment-delete-traits', args=[environment.api_key])

        # When
        self.client.post(url, data={'key': trait_to_delete})

        # Then
        assert not Trait.objects.filter(identity=identity, trait_key=trait_to_delete).exists()

        # and
        assert Trait.objects.filter(identity=identity, trait_key=trait_to_persist).exists()

    def test_user_can_list_environment_permission(self):
        # Given
        url = reverse('api-v1:environments:environment-permissions')

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1  # hard code how many permissions we expect there to be

    def test_environment_user_can_get_their_permissions(self):
        # Given
        user = FFAdminUser.objects.create(email='new-test@test.com')
        user.add_organisation(self.organisation)
        environment = Environment.objects.create(name='Test environment', project=self.project)
        user_permission = UserEnvironmentPermission.objects.create(user=user, environment=environment)
        user_permission.add_permission('VIEW_ENVIRONMENT')
        url = reverse('api-v1:environments:environment-my-permissions', args=[environment.api_key])

        # When
        self.client.force_authenticate(user)
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert not response.json()['admin']
        assert 'VIEW_ENVIRONMENT' in response.json()['permissions']


class SDKTraitsTest(APITestCase):
    JSON = 'application/json'

    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test organisation')
        project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test environment', project=project)
        self.identity = Identity.objects.create(identifier='test-user', environment=self.environment)
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        self.trait_key = 'trait_key'
        self.trait_value = 'trait_value'

    def test_can_set_trait_for_an_identity(self):
        # Given
        url = reverse('api-v1:sdk-traits-list')

        # When
        res = self.client.post(
            url, data=self._generate_json_trait_data(), content_type=self.JSON
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Trait.objects.filter(
            identity=self.identity, trait_key=self.trait_key
        ).exists()

    def test_cannot_set_trait_for_an_identity_for_organisations_without_persistence(
        self
    ):
        # Given
        url = reverse('api-v1:sdk-traits-list')

        # an organisation that is configured to not store traits
        self.organisation.persist_trait_data = False
        self.organisation.save()

        # When
        response = self.client.post(
            url, data=self._generate_json_trait_data(), content_type=self.JSON
        )

        # Then
        # the request fails
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_json = response.json()
        assert response_json['detail'] == (
            'Organisation is not authorised to store traits.'
        )

        # and no traits are stored
        assert Trait.objects.count() == 0

    def test_can_set_trait_with_boolean_value_for_an_identity(self):
        # Given
        url = reverse('api-v1:sdk-traits-list')
        trait_value = True

        # When
        res = self.client.post(url, data=self._generate_json_trait_data(trait_value=trait_value),
                               content_type=self.JSON)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Trait.objects.get(identity=self.identity, trait_key=self.trait_key).get_trait_value() == trait_value

    def test_can_set_trait_with_identity_value_for_an_identity(self):
        # Given
        url = reverse('api-v1:sdk-traits-list')
        trait_value = 12

        # When
        res = self.client.post(url, data=self._generate_json_trait_data(trait_value=trait_value),
                               content_type=self.JSON)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Trait.objects.get(identity=self.identity, trait_key=self.trait_key).get_trait_value() == trait_value

    def test_add_trait_creates_identity_if_it_doesnt_exist(self):
        # Given
        url = reverse('api-v1:sdk-traits-list')
        identifier = 'new-identity'

        # When
        res = self.client.post(url, data=self._generate_json_trait_data(identifier=identifier), content_type=self.JSON)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Identity.objects.filter(identifier=identifier, environment=self.environment).exists()

        # and
        assert Trait.objects.filter(identity__identifier=identifier, trait_key=self.trait_key).exists()

    def test_trait_is_updated_if_already_exists(self):
        # Given
        url = reverse('api-v1:sdk-traits-list')
        trait = Trait.objects.create(trait_key=self.trait_key, value_type=STRING, string_value=self.trait_value,
                                     identity=self.identity)
        new_value = 'Some new value'

        # When
        self.client.post(url, data=self._generate_json_trait_data(trait_value=new_value), content_type=self.JSON)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == new_value

    def test_increment_value_increments_trait_value_if_value_positive_integer(self):
        # Given
        initial_value = 2
        increment_by = 2

        url = reverse('api-v1:sdk-traits-increment-value')
        trait = Trait.objects.create(identity=self.identity, trait_key=self.trait_key, value_type=INTEGER,
                                     integer_value=initial_value)
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': increment_by
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == initial_value + increment_by

    def test_increment_value_decrements_trait_value_if_value_negative_integer(self):
        # Given
        initial_value = 2
        increment_by = -2

        url = reverse('api-v1:sdk-traits-increment-value')
        trait = Trait.objects.create(identity=self.identity, trait_key=self.trait_key, value_type=INTEGER,
                                     integer_value=initial_value)
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': increment_by
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == initial_value + increment_by

    def test_increment_value_initialises_trait_with_a_value_of_zero_if_it_doesnt_exist(self):
        # Given
        increment_by = 1

        url = reverse('api-v1:sdk-traits-increment-value')
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': increment_by
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait = Trait.objects.get(trait_key=self.trait_key, identity=self.identity)
        assert trait.get_trait_value() == increment_by

    def test_increment_value_returns_400_if_trait_value_not_integer(self):
        # Given
        url = reverse('api-v1:sdk-traits-increment-value')
        Trait.objects.create(identity=self.identity, trait_key=self.trait_key, value_type=STRING, string_value='str')
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': 2
        }

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_create_traits(self):
        # Given
        num_traits = 20
        url = reverse('api-v1:sdk-traits-bulk-create')
        traits = [self._generate_trait_data(trait_key=f'trait_{i}') for i in range(num_traits)]

        # When
        response = self.client.put(url, data=json.dumps(traits), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Trait.objects.filter(identity=self.identity).count() == num_traits

    def test_sending_null_value_in_bulk_create_deletes_trait_for_identity(self):
        # Given
        url = reverse('api-v1:sdk-traits-bulk-create')
        trait_to_delete = Trait.objects.create(
            trait_key=self.trait_key,
            value_type=STRING,
            string_value=self.trait_value,
            identity=self.identity
        )
        trait_key_to_keep = "another_trait_key"
        trait_to_keep = Trait.objects.create(
            trait_key=trait_key_to_keep,
            value_type=STRING,
            string_value="value is irrelevant",
            identity=self.identity
        )
        data = [{
            'identity': {
                'identifier': self.identity.identifier
            },
            'trait_key': self.trait_key,
            'trait_value': None
        }]

        # When
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')

        # Then
        # the request is successful
        assert response.status_code == status.HTTP_200_OK

        # and the trait is deleted
        assert not Trait.objects.filter(id=trait_to_delete.id).exists()

        # but the trait missing from the request is left untouched
        assert Trait.objects.filter(id=trait_to_keep.id).exists()

    def _generate_trait_data(self, identifier=None, trait_key=None, trait_value=None):
        identifier = identifier or self.identity.identifier
        trait_key = trait_key or self.trait_key
        trait_value = trait_value or self.trait_value

        return {
            'identity': {
                'identifier': identifier
            },
            'trait_key': trait_key,
            'trait_value': trait_value
        }

    def _generate_json_trait_data(self, identifier=None, trait_key=None, trait_value=None):
        return json.dumps(self._generate_trait_data(identifier, trait_key, trait_value))


@pytest.mark.django_db
class TraitViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name='Test org')
        user.add_organisation(organisation, OrganisationRole.ADMIN)

        self.project = Project.objects.create(name='Test project', organisation=organisation)
        self.environment = Environment.objects.create(name='Test environment', project=self.project)
        self.identity = Identity.objects.create(identifier='test-user', environment=self.environment)

    def test_can_delete_trait(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        url = reverse('api-v1:environments:identities-traits-detail',
                      args=[self.environment.api_key, self.identity.id, trait.id])

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert not Trait.objects.filter(pk=trait.id).exists()

    def test_delete_trait_only_deletes_single_trait_if_query_param_not_provided(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        identity_2 = Identity.objects.create(identifier='test-user-2', environment=self.environment)

        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        trait_2 = Trait.objects.create(identity=identity_2, trait_key=trait_key, value_type=STRING,
                                       string_value=trait_value)

        url = reverse('api-v1:environments:identities-traits-detail',
                      args=[self.environment.api_key, self.identity.id, trait.id])

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert Trait.objects.filter(pk=trait_2.id).exists()

    def test_delete_trait_deletes_all_traits_if_query_param_provided(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        identity_2 = Identity.objects.create(identifier='test-user-2', environment=self.environment)

        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        trait_2 = Trait.objects.create(identity=identity_2, trait_key=trait_key, value_type=STRING,
                                       string_value=trait_value)

        base_url = reverse('api-v1:environments:identities-traits-detail',
                           args=[self.environment.api_key, self.identity.id, trait.id])
        url = base_url + '?deleteAllMatchingTraits=true'

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert not Trait.objects.filter(pk=trait_2.id).exists()

    def test_delete_trait_only_deletes_traits_in_current_environment(self):
        # Given
        environment_2 = Environment.objects.create(name='Test environment', project=self.project)
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        identity_2 = Identity.objects.create(identifier='test-user-2', environment=environment_2)

        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        trait_2 = Trait.objects.create(identity=identity_2, trait_key=trait_key, value_type=STRING,
                                       string_value=trait_value)

        base_url = reverse('api-v1:environments:identities-traits-detail',
                           args=[self.environment.api_key, self.identity.id, trait.id])
        url = base_url + '?deleteAllMatchingTraits=true'

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert Trait.objects.filter(pk=trait_2.id).exists()


@pytest.mark.django_db
class WebhookViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name='Test organisation')
        user.add_organisation(organisation, OrganisationRole.ADMIN)

        project = Project.objects.create(name='Test project', organisation=organisation)
        self.environment = Environment.objects.create(name='Test environment', project=project)

        self.valid_webhook_url = 'http://my.webhook.com/webhooks'

    def test_can_create_webhook_for_an_environment(self):
        # Given
        url = reverse('api-v1:environments:environment-webhooks-list', args=[self.environment.api_key])
        data = {
            'url': self.valid_webhook_url,
            'enabled': True
        }

        # When
        res = self.client.post(url, data)

        # Then
        assert res.status_code == status.HTTP_201_CREATED

        # and
        assert Webhook.objects.filter(environment=self.environment, **data).exists()

    def test_can_update_webhook_for_an_environment(self):
        # Given
        webhook = Webhook.objects.create(url=self.valid_webhook_url, environment=self.environment)
        url = reverse('api-v1:environments:environment-webhooks-detail', args=[self.environment.api_key, webhook.id])
        data = {
            'url': 'http://my.new.url.com/wehbooks',
            'enabled': False
        }

        # When
        res = self.client.put(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        webhook.refresh_from_db()
        assert webhook.url == data['url'] and not webhook.enabled

    def test_can_delete_webhook_for_an_environment(self):
        # Given
        webhook = Webhook.objects.create(url=self.valid_webhook_url, environment=self.environment)
        url = reverse('api-v1:environments:environment-webhooks-detail', args=[self.environment.api_key, webhook.id])

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert not Webhook.objects.filter(id=webhook.id).exists()

    def test_can_list_webhooks_for_an_environment(self):
        # Given
        webhook = Webhook.objects.create(url=self.valid_webhook_url, environment=self.environment)
        url = reverse('api-v1:environments:environment-webhooks-list', args=[self.environment.api_key])

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert res.json()[0]['id'] == webhook.id

    def test_cannot_delete_webhooks_for_environment_user_does_not_belong_to(self):
        # Given
        new_organisation = Organisation.objects.create(name='New organisation')
        new_project = Project.objects.create(name='New project', organisation=new_organisation)
        new_environment = Environment.objects.create(name='New Environment', project=new_project)
        webhook = Webhook.objects.create(url=self.valid_webhook_url, environment=new_environment)
        url = reverse('api-v1:environments:environment-webhooks-detail', args=[self.environment.api_key, webhook.id])

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # and
        assert Webhook.objects.filter(id=webhook.id).exists()


