import json
from datetime import datetime
from unittest import TestCase, mock

import pytest
import pytz
from django.forms import model_to_dict
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from audit.models import (
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE,
    IDENTITY_FEATURE_STATE_UPDATED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from environments.identities.models import Identity
from environments.models import Environment
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from organisations.models import Organisation, OrganisationRole
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from projects.tags.models import Tag
from segments.models import Segment
from users.models import FFAdminUser
from util.tests import Helper
from webhooks.webhooks import WebhookEventType

# patch this function as it's triggering extra threads and causing errors
mock.patch("features.signals.trigger_feature_state_change_webhooks").start()


@pytest.mark.django_db
class ProjectFeatureTestCase(TestCase):
    project_features_url = "/api/v1/projects/%s/features/"
    project_feature_detail_url = "/api/v1/projects/%s/features/%d/"
    post_template = '{ "name": "%s", "project": %d, "initial_value": "%s" }'

    def setUp(self):
        self.client = APIClient()
        self.user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=self.user)

        self.organisation = Organisation.objects.create(name="Test Org")

        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.project2 = Project.objects.create(
            name="Test project2", organisation=self.organisation
        )
        self.environment_1 = Environment.objects.create(
            name="Test environment 1", project=self.project
        )
        self.environment_2 = Environment.objects.create(
            name="Test environment 2", project=self.project
        )

        self.tag_one = Tag.objects.create(
            label="Test Tag",
            color="#fffff",
            description="Test Tag description",
            project=self.project,
        )
        self.tag_two = Tag.objects.create(
            label="Test Tag2",
            color="#fffff",
            description="Test Tag2 description",
            project=self.project,
        )
        self.tag_other_project = Tag.objects.create(
            label="Wrong Tag",
            color="#fffff",
            description="Test Tag description",
            project=self.project2,
        )

    def test_owners_is_read_only_for_feature_create(self):
        # Given - set up data
        default_value = "This is a value"
        data = {
            "name": "test feature",
            "initial_value": default_value,
            "project": self.project.id,
            "owners": [
                {
                    "id": 2,
                    "email": "fake_user@mail.com",
                    "first_name": "fake",
                    "last_name": "user",
                }
            ],
        }
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.json()["owners"]) == 1
        assert response.json()["owners"][0]["id"] == self.user.id
        assert response.json()["owners"][0]["email"] == self.user.email

    @mock.patch("features.views.trigger_feature_state_change_webhooks")
    def test_feature_state_webhook_triggered_when_feature_deleted(
        self, mocked_trigger_fs_change_webhook
    ):
        # Given
        feature = Feature.objects.create(name="test feature", project=self.project)
        feature_states = list(feature.feature_states.all())
        # When
        self.client.delete(
            self.project_feature_detail_url % (self.project.id, feature.id)
        )
        # Then
        mock_calls = [
            mock.call(fs, WebhookEventType.FLAG_DELETED) for fs in feature_states
        ]
        mocked_trigger_fs_change_webhook.has_calls(mock_calls)

    def test_remove_owners_only_remove_specified_owners(self):
        # Given
        user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
        user_3 = FFAdminUser.objects.create_user(email="user3@mail.com")
        feature = Feature.objects.create(name="Test Feature", project=self.project)
        feature.owners.add(user_2, user_3)

        url = reverse(
            "api-v1:projects:project-features-remove-owners",
            args=[self.project.id, feature.id],
        )
        data = {"user_ids": [user_2.id]}
        # When
        json_response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        ).json()
        assert len(json_response["owners"]) == 1
        assert json_response["owners"][0] == {
            "id": user_3.id,
            "email": user_3.email,
            "first_name": user_3.first_name,
            "last_name": user_3.last_name,
        }

    def test_audit_log_created_when_feature_state_created_for_identity(self):
        # Given
        feature = Feature.objects.create(name="Test feature", project=self.project)
        identity = Identity.objects.create(
            identifier="test-identifier", environment=self.environment_1
        )
        url = reverse(
            "api-v1:environments:identity-featurestates-list",
            args=[self.environment_1.api_key, identity.id],
        )
        data = {"feature": feature.id, "enabled": True}

        # When
        self.client.post(url, data=json.dumps(data), content_type="application/json")

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.FEATURE_STATE.name
            ).count()
            == 1
        )

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (
            feature.name,
            identity.identifier,
        )
        audit_log = AuditLog.objects.get(
            related_object_type=RelatedObjectType.FEATURE_STATE.name
        )
        assert audit_log.log == expected_log_message

    def test_audit_log_created_when_feature_state_updated_for_identity(self):
        # Given
        feature = Feature.objects.create(name="Test feature", project=self.project)
        identity = Identity.objects.create(
            identifier="test-identifier", environment=self.environment_1
        )
        feature_state = FeatureState.objects.create(
            feature=feature,
            environment=self.environment_1,
            identity=identity,
            enabled=True,
        )
        url = reverse(
            "api-v1:environments:identity-featurestates-detail",
            args=[self.environment_1.api_key, identity.id, feature_state.id],
        )
        data = {"feature": feature.id, "enabled": False}

        # When
        self.client.put(url, data=json.dumps(data), content_type="application/json")

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.FEATURE_STATE.name
            ).count()
            == 1
        )

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (
            feature.name,
            identity.identifier,
        )
        audit_log = AuditLog.objects.get(
            related_object_type=RelatedObjectType.FEATURE_STATE.name
        )
        assert audit_log.log == expected_log_message

    def test_audit_log_created_when_feature_state_deleted_for_identity(self):
        # Given
        feature = Feature.objects.create(name="Test feature", project=self.project)
        identity = Identity.objects.create(
            identifier="test-identifier", environment=self.environment_1
        )
        feature_state = FeatureState.objects.create(
            feature=feature,
            environment=self.environment_1,
            identity=identity,
            enabled=True,
        )
        url = reverse(
            "api-v1:environments:identity-featurestates-detail",
            args=[self.environment_1.api_key, identity.id, feature_state.id],
        )

        # When
        self.client.delete(url)

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.FEATURE_STATE.name
            ).count()
            == 1
        )

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_DELETED_MESSAGE % (
            feature.name,
            identity.identifier,
        )
        audit_log = AuditLog.objects.get(
            related_object_type=RelatedObjectType.FEATURE_STATE.name
        )
        assert audit_log.log == expected_log_message

    def test_when_add_tags_from_different_project_on_feature_create_then_failed(self):
        # Given - set up data
        feature_name = "test feature"
        data = {
            "name": feature_name,
            "project": self.project.id,
            "initial_value": "test",
            "tags": [self.tag_other_project.id],
        }

        # When
        response = self.client.post(
            self.project_features_url % self.project.id,
            data=json.dumps(data),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # check no feature was created successfully
        assert (
            Feature.objects.filter(name=feature_name, project=self.project.id).count()
            == 0
        )

    def test_when_add_tags_on_feature_update_then_success(self):
        # Given - set up data
        feature = Feature.objects.create(project=self.project, name="test feature")
        data = {
            "name": feature.name,
            "project": self.project.id,
            "tags": [self.tag_one.id],
        }

        # When
        response = self.client.put(
            self.project_feature_detail_url % (self.project.id, feature.id),
            data=json.dumps(data),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        # check feature was created successfully
        check_feature = Feature.objects.filter(
            name=feature.name, project=self.project.id
        ).first()

        # check tags added
        assert check_feature.tags.count() == 1

    def test_when_add_tags_from_different_project_on_feature_update_then_failed(self):
        # Given - set up data
        feature = Feature.objects.create(project=self.project, name="test feature")
        data = {
            "name": feature.name,
            "project": self.project.id,
            "tags": [self.tag_other_project.id],
        }

        # When
        response = self.client.put(
            self.project_feature_detail_url % (self.project.id, feature.id),
            data=json.dumps(data),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # check feature was created successfully
        check_feature = Feature.objects.filter(
            name=feature.name, project=self.project.id
        ).first()

        # check tags not added
        assert check_feature.tags.count() == 0

    def test_list_features_is_archived_filter(self):
        # Firstly, let's setup the initial data
        feature = Feature.objects.create(name="test_feature", project=self.project)
        archived_feature = Feature.objects.create(
            name="archived_feature", project=self.project, is_archived=True
        )
        base_url = reverse(
            "api-v1:projects:project-features-list", args=[self.project.id]
        )
        # Next, let's test true filter
        url = f"{base_url}?is_archived=true"
        response = self.client.get(url)
        assert len(response.json()["results"]) == 1
        assert response.json()["results"][0]["id"] == archived_feature.id

        # Finally, let's test false filter
        url = f"{base_url}?is_archived=false"
        response = self.client.get(url)
        assert len(response.json()["results"]) == 1
        assert response.json()["results"][0]["id"] == feature.id

    def test_put_feature_does_not_update_feature_states(self):
        # Given
        feature = Feature.objects.create(
            name="test_feature", project=self.project, default_enabled=False
        )
        url = reverse(
            "api-v1:projects:project-features-detail",
            args=[self.project.id, feature.id],
        )
        data = model_to_dict(feature)
        data["default_enabled"] = True

        # When
        response = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        assert all(fs.enabled is False for fs in feature.feature_states.all())

    @mock.patch("features.views.get_multiple_event_list_for_feature")
    def test_get_influx_data(self, mock_get_event_list):
        # Given
        feature = Feature.objects.create(name="test_feature", project=self.project)
        base_url = reverse(
            "api-v1:projects:project-features-get-influx-data",
            args=[self.project.id, feature.id],
        )
        url = f"{base_url}?environment_id={self.environment_1.id}"

        mock_get_event_list.return_value = [
            {
                feature.name: 1,
                "datetime": datetime(2021, 2, 26, 12, 0, 0, tzinfo=pytz.UTC),
            }
        ]

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        mock_get_event_list.assert_called_once_with(
            feature_name=feature.name,
            environment_id=str(self.environment_1.id),  # provided as a GET param
            period="24h",  # this is the default but can be provided as a GET param
            aggregate_every="24h",  # this is the default but can be provided as a GET param
        )

    def test_project_admin_can_create_mv_options_when_creating_feature(self):
        # Given
        data = {
            "name": "test_feature",
            "default_enabled": True,
            "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
        }
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        response_json = response.json()
        assert len(response_json["multivariate_options"]) == 1

    def test_regular_user_cannot_create_mv_options_when_creating_feature(self):
        # Given
        user = FFAdminUser.objects.create(email="regularuser@project.com")
        user.add_organisation(self.organisation)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=self.project
        )
        permissions = PermissionModel.objects.filter(
            key__in=["VIEW_PROJECT", "CREATE_FEATURE"]
        )
        user_project_permission.permissions.add(*permissions)
        client = APIClient()
        client.force_authenticate(user)

        data = {
            "name": "test_feature",
            "default_enabled": True,
            "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
        }
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_user_cannot_create_mv_options_when_updating_feature(self):
        # Given
        user = FFAdminUser.objects.create(email="regularuser@project.com")
        user.add_organisation(self.organisation)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=self.project
        )
        permissions = PermissionModel.objects.filter(
            key__in=["VIEW_PROJECT", "CREATE_FEATURE"]
        )
        user_project_permission.permissions.add(*permissions)
        client = APIClient()
        client.force_authenticate(user)

        feature = Feature.objects.create(
            project=self.project,
            name="a_feature",
            default_enabled=True,
        )

        data = {
            "name": feature.name,
            "default_enabled": feature.default_enabled,
            "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
        }
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_user_can_update_feature_description(self):
        # Given
        user = FFAdminUser.objects.create(email="regularuser@project.com")
        user.add_organisation(self.organisation)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=self.project
        )
        permissions = PermissionModel.objects.filter(
            key__in=["VIEW_PROJECT", "CREATE_FEATURE"]
        )
        user_project_permission.permissions.add(*permissions)
        client = APIClient()
        client.force_authenticate(user)

        feature = Feature.objects.create(
            project=self.project,
            name="a_feature",
            default_enabled=True,
        )

        data = {
            "name": feature.name,
            "default_enabled": feature.default_enabled,
            "description": "a description",
        }

        url = reverse(
            "api-v1:projects:project-features-detail",
            args=[self.project.id, feature.id],
        )

        # When
        response = client.put(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        feature.refresh_from_db()
        assert feature.description == data["description"]

    @mock.patch("environments.models.environment_wrapper")
    def test_create_feature_only_triggers_write_to_dynamodb_once_per_environment(
        self, mock_dynamo_environment_wrapper
    ):
        # Given
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])
        data = {"name": "Test feature flag", "type": "FLAG", "project": self.project.id}

        self.project.enable_dynamo_db = True
        self.project.save()

        mock_dynamo_environment_wrapper.is_enabled = True
        mock_dynamo_environment_wrapper.reset_mock()

        # When
        self.client.post(url, data=data)

        # Then
        mock_dynamo_environment_wrapper.write_environments.assert_called_once()


@pytest.mark.django_db
class SDKFeatureStatesTestCase(APITestCase):
    def setUp(self) -> None:
        self.environment_fs_value = "environment"
        self.identity_fs_value = "identity"
        self.segment_fs_value = "segment"

        self.organisation = Organisation.objects.create(name="Test organisation")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test environment", project=self.project
        )
        self.feature = Feature.objects.create(
            name="Test feature",
            project=self.project,
            initial_value=self.environment_fs_value,
        )
        segment = Segment.objects.create(name="Test segment", project=self.project)
        feature_segment = FeatureSegment.objects.create(
            segment=segment,
            feature=self.feature,
            environment=self.environment,
        )
        segment_feature_state = FeatureState.objects.create(
            feature=self.feature,
            feature_segment=feature_segment,
            environment=self.environment,
        )
        FeatureStateValue.objects.filter(feature_state=segment_feature_state).update(
            string_value=self.segment_fs_value
        )
        identity = Identity.objects.create(
            identifier="test", environment=self.environment
        )
        identity_feature_state = FeatureState.objects.create(
            identity=identity, environment=self.environment, feature=self.feature
        )
        FeatureStateValue.objects.filter(feature_state=identity_feature_state).update(
            string_value=self.identity_fs_value
        )

        self.url = reverse("api-v1:flags")

        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)

    def test_get_flags(self):
        # Given - setup data which includes a single feature overridden by a segment and an identity

        # When - we get flags
        response = self.client.get(self.url)

        # Then - we only get a single flag back and that is the environment default
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["feature"]["id"] == self.feature.id
        assert response_json[0]["feature_state_value"] == self.environment_fs_value

    def test_get_flags_exclude_disabled(self):

        # Given
        # a project with hide_disabled_flags enabled
        project_flag_disabled = Project.objects.create(
            name="Project Flag Disabled",
            organisation=self.organisation,
            hide_disabled_flags=True,
        )

        # and a set of features and environments for that project
        other_environment = Environment.objects.create(
            name="Test Environment 2", project=project_flag_disabled
        )
        disabled_flag = Feature.objects.create(
            name="Flag 1", project=project_flag_disabled
        )
        enabled_flag = Feature.objects.create(
            name="Flag 2", project=project_flag_disabled, default_enabled=True
        )

        # When
        # we get all flags for an environment
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=other_environment.api_key)
        response = self.client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert len(response_json) == 1

        # disabled flags are not returned
        for flag in response_json:
            assert flag["feature"]["id"] != disabled_flag.id

        # but enabled ones are
        assert response_json[0]["feature"]["id"] == enabled_flag.id
