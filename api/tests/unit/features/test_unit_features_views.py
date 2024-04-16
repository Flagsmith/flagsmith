import json
import uuid
from datetime import date, datetime, timedelta
from unittest import TestCase, mock

import pytest
import pytz
from app_analytics.dataclasses import FeatureEvaluationData
from core.constants import FLAGSMITH_UPDATED_AT_HEADER
from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from pytest_django import DjangoAssertNumQueries
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from audit.constants import (
    FEATURE_DELETED_MESSAGE,
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE,
    IDENTITY_FEATURE_STATE_UPDATED_MESSAGE,
)
from audit.models import AuditLog, RelatedObjectType
from environments.identities.models import Identity
from environments.models import Environment, EnvironmentAPIKey
from environments.permissions.constants import (
    MANAGE_SEGMENT_OVERRIDES,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from environments.permissions.models import UserEnvironmentPermission
from features.feature_types import MULTIVARIATE
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import BOOLEAN, INTEGER, STRING
from features.versioning.models import EnvironmentFeatureVersion
from organisations.models import Organisation, OrganisationRole
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from projects.permissions import CREATE_FEATURE, VIEW_PROJECT
from projects.tags.models import Tag
from segments.models import Segment
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser, UserPermissionGroup
from util.tests import Helper
from webhooks.webhooks import WebhookEventType

# patch this function as it's triggering extra threads and causing errors
mock.patch("features.signals.trigger_feature_state_change_webhooks").start()

now = timezone.now()
two_hours_ago = now - timedelta(hours=2)
one_hour_ago = now - timedelta(hours=1)


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
        mocked_trigger_fs_change_webhook.assert_has_calls(mock_calls)

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
            "last_login": None,
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
                log=IDENTITY_FEATURE_STATE_DELETED_MESSAGE
                % (
                    feature.name,
                    identity.identifier,
                )
            ).count()
            == 1
        )

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

    def test_regular_user_cannot_create_mv_options_when_creating_feature(self):
        # Given
        user = FFAdminUser.objects.create(email="regularuser@project.com")
        user.add_organisation(self.organisation)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=self.project
        )
        permissions = PermissionModel.objects.filter(
            key__in=[VIEW_PROJECT, CREATE_FEATURE]
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
            key__in=[VIEW_PROJECT, CREATE_FEATURE]
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
            key__in=[VIEW_PROJECT, CREATE_FEATURE]
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
        # refresh the last_updated_at
        self.environment.refresh_from_db()
        assert response.headers[FLAGSMITH_UPDATED_AT_HEADER] == str(
            self.environment.updated_at.timestamp()
        )


@pytest.mark.parametrize(
    "environment_value, project_value, disabled_flag_returned",
    (
        (True, True, False),
        (True, False, False),
        (False, True, True),
        (False, False, True),
        (None, True, False),
        (None, False, True),
    ),
)
def test_get_flags_hide_disabled_flags(
    environment_value,
    project_value,
    disabled_flag_returned,
    project,
    environment,
    api_client,
):
    # Given
    project.hide_disabled_flags = project_value
    project.save()

    environment.hide_disabled_flags = environment_value
    environment.save()

    Feature.objects.create(name="disabled_flag", project=project, default_enabled=False)
    Feature.objects.create(name="enabled_flag", project=project, default_enabled=True)

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == (2 if disabled_flag_returned else 1)


def test_get_flags_hide_sensitive_data(api_client, environment, feature):
    # Given
    environment.hide_sensitive_data = True
    environment.save()

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)
    feature_sensitive_fields = [
        "created_date",
        "description",
        "initial_value",
        "default_enabled",
    ]
    fs_sensitive_fields = ["id", "environment", "identity", "feature_segment"]

    # Then
    assert response.status_code == status.HTTP_200_OK
    # Check that the sensitive fields are None
    for flag in response.json():
        for field in fs_sensitive_fields:
            assert flag[field] is None

        for field in feature_sensitive_fields:
            assert flag["feature"][field] is None


def test_get_flags__server_key_only_feature__return_expected(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature.is_server_key_only = True
    feature.save()

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not response.json()


def test_get_flags__server_key_only_feature__server_key_auth__return_expected(
    api_client: APIClient,
    environment_api_key: EnvironmentAPIKey,
    feature: Feature,
) -> None:
    # Given
    feature.is_server_key_only = True
    feature.save()

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_get_feature_states_by_uuid(client, environment, feature, feature_state):
    # Given
    url = reverse(
        "api-v1:features:get-feature-state-by-uuid", args=[feature_state.uuid]
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["uuid"] == str(feature_state.uuid)


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_deleted_features_are_not_listed(client, project, environment, feature):
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    feature.delete()

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_get_feature_evaluation_data(project, feature, environment, mocker, client):
    # Given
    base_url = reverse(
        "api-v1:projects:project-features-get-evaluation-data",
        args=[project.id, feature.id],
    )
    url = f"{base_url}?environment_id={environment.id}"
    mocked_get_feature_evaluation_data = mocker.patch(
        "features.views.get_feature_evaluation_data", autospec=True
    )
    mocked_get_feature_evaluation_data.return_value = [
        FeatureEvaluationData(count=10, day=date.today()),
        FeatureEvaluationData(count=10, day=date.today() - timedelta(days=1)),
    ]
    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    assert response.json()[0] == {"day": str(date.today()), "count": 10}
    assert response.json()[1] == {
        "day": str(date.today() - timedelta(days=1)),
        "count": 10,
    }
    mocked_get_feature_evaluation_data.assert_called_with(
        feature=feature, period=30, environment_id=environment.id
    )


def test_create_segment_override_forbidden(
    feature: Feature,
    segment: Segment,
    environment: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    # When
    enabled = True
    string_value = "foo"
    data = {
        "feature_state_value": {"string_value": string_value},
        "enabled": enabled,
        "feature_segment": {"segment": segment.id},
    }

    # Staff client lacks permission to create segment.
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 403
    assert response.data == {
        "detail": "You do not have permission to perform this action."
    }


def test_create_segment_override_staff(
    feature: Feature,
    segment: Segment,
    environment: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    # When
    enabled = True
    string_value = "foo"
    data = {
        "feature_state_value": {"string_value": string_value},
        "enabled": enabled,
        "feature_segment": {"segment": segment.id},
    }
    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=staff_user, admin=False, environment=environment
    )
    user_environment_permission.permissions.add(MANAGE_SEGMENT_OVERRIDES)

    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == 201
    assert response.data["feature_segment"]["segment"] == segment.id


def test_create_segment_override(admin_client, feature, segment, environment):
    # Given
    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    enabled = True
    string_value = "foo"
    data = {
        "feature_state_value": {"string_value": string_value},
        "enabled": enabled,
        "feature_segment": {"segment": segment.id},
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    created_override = FeatureState.objects.filter(
        feature=feature, environment=environment, feature_segment__segment=segment
    ).first()
    assert created_override is not None
    assert created_override.enabled is enabled
    assert created_override.get_feature_state_value() == string_value


def test_get_flags_is_not_throttled_by_user_throttle(
    api_client, environment, feature, settings
):
    # Given
    settings.REST_FRAMEWORK = {"DEFAULT_THROTTLE_RATES": {"user": "1/minute"}}
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    url = reverse("api-v1:flags")

    # When
    for _ in range(10):
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK


def test_list_feature_states_from_simple_view_set(
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    admin_client: APIClient,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    base_url = reverse("api-v1:features:featurestates-list")
    url = f"{base_url}?environment={environment.id}"

    # add another feature
    feature2 = Feature.objects.create(
        name="another_feature", project=environment.project
    )

    # and a new version for the same feature to check for N+1 issues
    v1_feature_state = FeatureState.objects.get(
        environment=environment, feature=feature2
    )
    v1_feature_state.clone(env=environment, version=2, live_from=timezone.now())

    # add another organisation with a project, environment and feature (which should be
    # excluded)
    another_organisation = Organisation.objects.create(name="another_organisation")
    admin_user.add_organisation(another_organisation)
    another_project = Project.objects.create(
        name="another_project", organisation=another_organisation
    )
    Environment.objects.create(name="another_environment", project=another_project)
    Feature.objects.create(project=another_project, name="another_projects_feature")
    UserProjectPermission.objects.create(
        user=admin_user, project=another_project, admin=True
    )

    # add another feature with multivariate options
    mv_feature = Feature.objects.create(
        name="mv_feature", project=environment.project, type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type="unicode",
        string_value="foo",
    )

    # When
    with django_assert_num_queries(9):
        response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


def test_list_feature_states_nested_environment_view_set(
    environment, project, feature, admin_client, django_assert_num_queries
):
    # Given
    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # Add an MV feature
    mv_feature = Feature.objects.create(
        name="mv_feature", project=project, type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type="unicode",
        string_value="foo",
    )

    # Add another feature
    second_feature = Feature.objects.create(name="another_feature", project=project)

    # create some new versions to test N+1 issues
    v1_feature_state = FeatureState.objects.get(
        feature=second_feature, environment=environment
    )
    v2_feature_state = v1_feature_state.clone(
        env=environment, version=2, live_from=timezone.now()
    )
    v2_feature_state.clone(env=environment, version=3, live_from=timezone.now())

    # When
    with django_assert_num_queries(8):
        response = admin_client.get(base_url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_filter_using_feature_name(
    environment, project, feature, client
):
    # Given
    Feature.objects.create(name="another_feature", project=project)
    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    url = f"{base_url}?feature_name={feature.name}"

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["feature"] == feature.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_filter_to_show_identity_override_only(
    environment, feature, client
):
    # Given
    FeatureState.objects.get(environment=environment, feature=feature)

    identifier = "test-identity"
    identity = Identity.objects.create(identifier=identifier, environment=environment)
    FeatureState.objects.create(
        environment=environment, feature=feature, identity=identity
    )

    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    url = base_url + "?anyIdentity&feature=" + str(feature.id)

    # When
    res = client.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK

    # and
    assert len(res.json().get("results")) == 1

    # and
    assert res.json()["results"][0]["identity"]["identifier"] == identifier


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_only_returns_latest_versions(
    environment, feature, client
):
    # Given
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)
    feature_state_v2 = feature_state.clone(
        env=environment, live_from=timezone.now(), version=2
    )

    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == feature_state_v2.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_does_not_return_null_versions(
    environment, feature, client
):
    # Given
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    FeatureState.objects.create(environment=environment, feature=feature, version=None)

    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == feature_state.id

    # Feature tests


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_default_is_archived_is_false(client, project):
    # Given - set up data
    data = {
        "name": "test feature",
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert response["is_archived"] is False


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_feature_is_archived(client, project, feature):
    # Given
    feature = Feature.objects.create(name="test feature", project=project)
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    data = {"name": "test feature", "is_archived": True}

    # When
    response = client.put(url, data=data).json()

    # Then
    assert response["is_archived"] is True


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_create_feature_states_when_feature_created(
    client, project, environment
):
    # Given - set up data
    environment_2 = Environment.objects.create(
        name="Test environment 2", project=project
    )
    default_value = "This is a value"
    data = {
        "name": "test feature",
        "initial_value": default_value,
        "project": project.id,
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    # check feature was created successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 1

    # check feature was added to environment
    assert FeatureState.objects.filter(environment=environment).count() == 1
    assert FeatureState.objects.filter(environment=environment_2).count() == 1

    # check that value was correctly added to feature state
    feature_state = FeatureState.objects.filter(environment=environment).first()
    assert feature_state.get_feature_state_value() == default_value


@pytest.mark.parametrize("default_value", [(12), (True), ("test")])
@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_create_feature_states_with_value_when_feature_created(
    client, project, environment, default_value
):
    # Given - set up data
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {
        "name": "test feature",
        "initial_value": default_value,
        "project": project.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    # check feature was created successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 1

    # check feature was added to environment
    assert FeatureState.objects.filter(environment=environment).count() == 1

    # check that value was correctly added to feature state
    feature_state = FeatureState.objects.filter(environment=environment).first()
    assert feature_state.get_feature_state_value() == default_value


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_delete_feature_states_when_feature_deleted(
    client, project, feature, environment
):
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )

    # When
    response = client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check feature was deleted successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 0

    # check feature was removed from all environments
    assert (
        FeatureState.objects.filter(environment=environment, feature=feature).count()
        == 0
    )
    assert (
        FeatureState.objects.filter(environment=environment, feature=feature).count()
        == 0
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_returns_201_if_name_matches_regex(client, project):
    # Given
    project.feature_name_regex = "^[a-z_]{18}$"
    project.save()

    # feature name that has 18 characters
    feature_name = "valid_feature_name"

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": feature_name, "type": "FLAG", "project": project.id}

    # When
    response = client.post(url, data=data)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_returns_400_if_name_does_not_matches_regex(client, project):
    # Given
    project.feature_name_regex = "^[a-z]{18}$"
    project.save()

    # feature name longer than 18 characters
    feature_name = "not_a_valid_feature_name"

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": feature_name, "type": "FLAG", "project": project.id}

    # When
    response = client.post(url, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["name"][0]
        == f"Feature name must match regex: {project.feature_name_regex}"
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_feature_created(client, project, environment):
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": "Test feature flag", "type": "FLAG", "project": project.id}

    # When
    response = client.post(url, data=data)
    feature_id = response.json()["id"]

    # Then

    # Audit log exists for the feature
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name,
            related_object_id=feature_id,
        ).count()
        == 1
    )
    # and Audit log exists for every environment
    assert AuditLog.objects.filter(
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        project=project,
        environment__in=project.environments.all(),
    ).count() == len(project.environments.all())


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_feature_updated(client, project, feature):
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    data = {
        "name": "Test Feature updated",
        "type": "FLAG",
        "project": project.id,
    }

    # When
    client.put(url, data=data)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_logs_created_when_feature_deleted(client, project, feature):
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    feature_states_ids = list(feature.feature_states.values_list("id", flat=True))

    # When
    client.delete(url)

    # Then
    # Audit log exists for the feature
    assert AuditLog.objects.get(
        related_object_type=RelatedObjectType.FEATURE.name,
        related_object_id=feature.id,
        log=FEATURE_DELETED_MESSAGE % feature.name,
    )
    # and audit logs exists for all feature states for that feature
    assert AuditLog.objects.filter(
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        related_object_id__in=feature_states_ids,
        log=FEATURE_DELETED_MESSAGE % feature.name,
    ).count() == len(feature_states_ids)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_create_tags_when_feature_created(client, project, tag_one, tag_two):
    # Given - set up data
    default_value = "Test"
    feature_name = "Test feature"
    data = {
        "name": feature_name,
        "project": project.id,
        "initial_value": default_value,
        "tags": [tag_one.id, tag_two.id],
    }

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    # check feature was created successfully
    feature = Feature.objects.filter(name=feature_name, project=project.id).first()

    # check feature is tagged
    assert feature.tags.count() == 2
    assert list(feature.tags.all()) == [tag_one, tag_two]


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_add_owners_fails_if_user_not_found(client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)

    # Users have no association to the project or organisation.
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
    url = reverse(
        "api-v1:projects:project-features-add-owners",
        args=[project.id, feature.id],
    )
    data = {"user_ids": [user_1.id, user_2.id]}

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == ["Some users not found"]
    assert feature.owners.filter(id__in=[user_1.id, user_2.id]).count() == 0


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_add_owners_adds_owner(staff_user, admin_user, client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    UserProjectPermission.objects.create(
        user=staff_user, project=project
    ).add_permission(VIEW_PROJECT)

    url = reverse(
        "api-v1:projects:project-features-add-owners",
        args=[project.id, feature.id],
    )
    data = {"user_ids": [staff_user.id, admin_user.id]}

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    json_response = response.json()
    # Then
    assert len(json_response["owners"]) == 2
    assert json_response["owners"][0] == {
        "id": staff_user.id,
        "email": staff_user.email,
        "first_name": staff_user.first_name,
        "last_name": staff_user.last_name,
        "last_login": None,
    }
    assert json_response["owners"][1] == {
        "id": admin_user.id,
        "email": admin_user.email,
        "first_name": admin_user.first_name,
        "last_name": admin_user.last_name,
        "last_login": None,
    }


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_add_group_owners_adds_group_owner(client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Second Group", organisation=organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)
    group_2.users.add(user_1)

    url = reverse(
        "api-v1:projects:project-features-add-group-owners",
        args=[project.id, feature.id],
    )

    data = {"group_ids": [group_1.id, group_2.id]}

    # When
    json_response = client.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["group_owners"]) == 2
    assert json_response["group_owners"][0] == {
        "id": group_1.id,
        "name": group_1.name,
    }
    assert json_response["group_owners"][1] == {
        "id": group_2.id,
        "name": group_2.name,
    }


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_remove_group_owners_removes_group_owner(client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="To be removed group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="To be kept group", organisation=organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)
    group_2.users.add(user_1)

    feature.group_owners.add(group_1.id, group_2.id)

    url = reverse(
        "api-v1:projects:project-features-remove-group-owners",
        args=[project.id, feature.id],
    )

    # Note that only group_1 is set to be removed.
    data = {"group_ids": [group_1.id]}

    # When
    json_response = client.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["group_owners"]) == 1
    assert json_response["group_owners"][0] == {
        "id": group_2.id,
        "name": group_2.name,
    }


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_remove_group_owners_when_nonexistent(client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="To be removed group", organisation=organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)

    assert feature.group_owners.count() == 0

    url = reverse(
        "api-v1:projects:project-features-remove-group-owners",
        args=[project.id, feature.id],
    )

    # Note that group_1 is not present, but it should work
    # anyway since there may have been a double request or two
    # users working at the same time.
    data = {"group_ids": [group_1.id]}

    # When
    json_response = client.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["group_owners"]) == 0


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_add_group_owners_with_wrong_org_group(client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
    organisation = project.organisation
    other_organisation = Organisation.objects.create(name="Orgy")

    group_1 = UserPermissionGroup.objects.create(
        name="Valid Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Invalid Group", organisation=other_organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    user_2.add_organisation(other_organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)
    group_2.users.add(user_2)

    url = reverse(
        "api-v1:projects:project-features-add-group-owners",
        args=[project.id, feature.id],
    )

    data = {"group_ids": [group_1.id, group_2.id]}

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == 400
    response.json() == {"non_field_errors": ["Some groups not found"]}


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_list_features_return_tags(client, project, feature):
    # Given
    Feature.objects.create(name="test_feature", project=project)
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    feature = response_json["results"][0]
    assert "tags" in feature


def test_list_features_group_owners(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    feature = Feature.objects.create(name="test_feature", project=project)
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Second Group", organisation=organisation
    )
    feature.group_owners.add(group_1.id, group_2.id)

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    feature = response_json["results"][1]
    assert feature["group_owners"][0] == {
        "id": group_1.id,
        "name": group_1.name,
    }
    assert feature["group_owners"][1] == {
        "id": group_2.id,
        "name": group_2.name,
    }


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_project_admin_can_create_mv_options_when_creating_feature(client, project):
    # Given
    data = {
        "name": "test_feature",
        "default_enabled": True,
        "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert len(response_json["multivariate_options"]) == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_feature_by_uuid(client, project, feature):
    # Given
    url = reverse("api-v1:features:get-feature-by-uuid", args=[feature.uuid])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == feature.id
    assert response.json()["uuid"] == str(feature.uuid)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_feature_by_uuid_returns_404_if_feature_does_not_exists(client, project):
    # Given
    url = reverse("api-v1:features:get-feature-by-uuid", args=[uuid.uuid4()])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_feature_state_value_triggers_dynamo_rebuild(
    client, project, environment, feature, feature_state, settings, mocker
):
    # Given
    project.enable_dynamo_db = True
    project.save()

    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )
    mock_dynamo_environment_wrapper = mocker.patch(
        "environments.models.environment_wrapper"
    )

    # When
    response = client.patch(
        url,
        data=json.dumps({"feature_state_value": "new value"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    mock_dynamo_environment_wrapper.write_environments.assert_called_once()


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_overrides_creates_correct_audit_log_messages(
    client, feature, segment, environment
):
    # Given
    another_segment = Segment.objects.create(
        name="Another segment", project=segment.project
    )

    feature_segments_url = reverse("api-v1:features:feature-segment-list")
    feature_states_url = reverse("api-v1:features:featurestates-list")

    # When
    # we create 2 segment overrides for the feature
    for _segment in (segment, another_segment):
        feature_segment_response = client.post(
            feature_segments_url,
            data={
                "feature": feature.id,
                "segment": _segment.id,
                "environment": environment.id,
            },
        )
        assert feature_segment_response.status_code == status.HTTP_201_CREATED
        feature_segment_id = feature_segment_response.json()["id"]
        feature_state_response = client.post(
            feature_states_url,
            data={
                "feature": feature.id,
                "feature_segment": feature_segment_id,
                "environment": environment.id,
                "enabled": True,
            },
        )
        assert feature_state_response.status_code == status.HTTP_201_CREATED

    # Then
    assert AuditLog.objects.count() == 2
    assert (
        AuditLog.objects.filter(
            log=f"Flag state / Remote config value updated for feature "
            f"'{feature.name}' and segment '{segment.name}'"
        ).count()
        == 1
    )
    assert (
        AuditLog.objects.filter(
            log=f"Flag state / Remote config value updated for feature "
            f"'{feature.name}' and segment '{another_segment.name}'"
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_list_features_provides_information_on_number_of_overrides(
    feature,
    segment,
    segment_featurestate,
    identity,
    identity_featurestate,
    project,
    environment,
    client,
):
    # Given
    url = "%s?environment=%d" % (
        reverse("api-v1:projects:project-features-list", args=[project.id]),
        environment.id,
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["num_segment_overrides"] == 1
    assert response_json["results"][0]["num_identity_overrides"] == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_list_features_provides_segment_overrides_for_dynamo_enabled_project(
    dynamo_enabled_project, dynamo_enabled_project_environment_one, client
):
    # Given
    feature = Feature.objects.create(
        name="test_feature", project=dynamo_enabled_project
    )
    segment = Segment.objects.create(
        name="test_segment", project=dynamo_enabled_project
    )
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=dynamo_enabled_project_environment_one,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=dynamo_enabled_project_environment_one,
        feature_segment=feature_segment,
    )
    url = "%s?environment=%d" % (
        reverse(
            "api-v1:projects:project-features-list", args=[dynamo_enabled_project.id]
        ),
        dynamo_enabled_project_environment_one.id,
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["num_segment_overrides"] == 1
    assert response_json["results"][0]["num_identity_overrides"] is None


def test_create_segment_override_reaching_max_limit(
    admin_client, feature, segment, project, environment, settings
):
    # Given
    project.max_segment_overrides_allowed = 1
    project.save()

    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    data = {
        "feature_state_value": {"string_value": "value"},
        "enabled": True,
        "feature_segment": {"segment": segment.id},
    }

    # Now, crate the first override
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Then
    # Try to create another override
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["environment"]
        == "The environment has reached the maximum allowed segments overrides limit."
    )
    assert environment.feature_segments.count() == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_reaching_max_limit(client, project, settings):
    # Given
    project.max_features_allowed = 1
    project.save()

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Now, crate the first feature
    response = client.post(url, data={"name": "test_feature", "project": project.id})
    assert response.status_code == status.HTTP_201_CREATED

    # Then
    # Try to create another feature
    response = client.post(url, data={"name": "second_feature", "project": project.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["project"]
        == "The Project has reached the maximum allowed features limit."
    )


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_create_segment_override_using_environment_viewset(
    client, environment, feature, feature_segment
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment.id,
        "identity": None,
        "feature_segment": feature_segment.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response.json()["feature_state_value"] == new_value


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_create_feature_state_for_feature_from_different_project(
    client, environment, project_two_feature, feature_segment, project_two
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": project_two_feature.id,
        "environment": environment.id,
        "identity": None,
        "feature_segment": feature_segment.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["feature"][0] == "Feature does not exist in project"


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_create_feature_state_environment_is_read_only(
    client, environment, feature, feature_segment, environment_two
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment_two.id,
        "feature_segment": feature_segment.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["environment"] == environment.id


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_create_feature_state_of_feature_from_different_project(
    client, environment, project_two_feature, feature_segment
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": project_two_feature.id,
        "environment": environment.id,
        "identity": None,
        "feature_segment": feature_segment.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["feature"][0] == "Feature does not exist in project"


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_create_feature_state_environment_field_is_read_only(
    client, environment, feature, feature_segment, environment_two
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment_two.id,
        "feature_segment": feature_segment.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["environment"] == environment.id


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_update_environment_of_a_feature_state(
    client, environment, feature, feature_state, environment_two
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )
    new_value = "new-value"
    data = {
        "id": feature_state.id,
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment_two.id,
        "identity": None,
        "feature_segment": None,
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then - it did not change the environment field on the feature state
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["environment"][0]
        == "Cannot change the environment of a feature state"
    )


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_update_feature_of_a_feature_state(
    client, environment, feature_state, feature, identity, project
):
    # Given
    another_feature = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    url = reverse("api-v1:features:featurestates-detail", args=[feature_state.id])

    feature_state_value = "New value"
    data = {
        "enabled": True,
        "feature_state_value": {"type": "unicode", "string_value": feature_state_value},
        "environment": environment.id,
        "feature": another_feature.id,
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert another_feature.feature_states.count() == 1
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["feature"][0] == "Cannot change the feature of a feature state"
    )


def test_create_segment_override__using_simple_feature_state_viewset__allows_manage_segment_overrides(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES])

    url = reverse("api-v1:features:featurestates-list")

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    assert FeatureState.objects.filter(
        feature=feature, environment=environment, feature_segment=feature_segment
    ).exists()


def test_create_segment_override__using_simple_feature_state_viewset__denies_update_feature_state(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])

    url = reverse("api-v1:features:featurestates-list")

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_segment_override__using_simple_feature_state_viewset__allows_manage_segment_overrides(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
    segment_featurestate: FeatureState,
) -> None:
    # Given
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES])

    url = reverse(
        "api-v1:features:featurestates-detail", args=[segment_featurestate.id]
    )

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert FeatureState.objects.filter(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=True,
        feature_state_value__string_value="foo",
    ).exists()


def test_update_segment_override__using_simple_feature_state_viewset__denies_update_feature_state(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
    segment_featurestate: FeatureState,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])

    url = reverse(
        "api-v1:features:featurestates-detail", args=[segment_featurestate.id]
    )

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_features_n_plus_1(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}"

    # add some more versions to test for N+1 issues
    v1_feature_state = FeatureState.objects.get(
        feature=feature, environment=environment
    )
    for i in range(2, 4):
        v1_feature_state.clone(env=environment, version=i, live_from=timezone.now())

    # When
    with django_assert_num_queries(16):
        response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_list_features_with_union_tag(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    tag1 = Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    tag2 = Tag.objects.create(
        label="Test Tag2",
        color="#fffff",
        description="Test Tag2 description",
        project=project,
    )
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature2.tags.add(tag1)
    feature3.tags.add(tag2)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = (
        f"{base_url}?environment={environment.id}&tags={tag1.id}"
        f",{tag2.id}&tag_strategy=UNION"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # The first feature has been filtered out of the results.
    assert len(response.data["results"]) == 2

    assert response.data["results"][0]["id"] == feature2.id
    assert response.data["results"][0]["tags"] == [tag1.id]
    assert response.data["results"][1]["id"] == feature3.id
    assert response.data["results"][1]["tags"] == [tag2.id]


def test_list_features_with_intersection_tag(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    tag1 = Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    tag2 = Tag.objects.create(
        label="Test Tag2",
        color="#fffff",
        description="Test Tag2 description",
        project=project,
    )
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature2.tags.add(tag1, tag2)
    feature3.tags.add(tag2)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = (
        f"{base_url}?environment={environment.id}&tags={tag1.id}"
        f",{tag2.id}&tag_strategy=INTERSECTION"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Only feature2 has both tags, so it is the only result.
    assert len(response.data["results"]) == 1

    assert response.data["results"][0]["id"] == feature2.id
    assert response.data["results"][0]["tags"] == [tag1.id, tag2.id]


def test_list_features_with_feature_state(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
    identity: Identity,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="fancy_feature", project=project, initial_value="gone"
    )

    Environment.objects.create(
        name="Out of test scope environment",
        project=project,
    )

    feature_state1 = feature.feature_states.filter(environment=environment).first()
    feature_state1.enabled = True
    feature_state1.version = 1
    feature_state1.save()

    feature_state_value1 = feature_state1.feature_state_value
    feature_state_value1.string_value = None
    feature_state_value1.integer_value = 1945
    feature_state_value1.type = INTEGER
    feature_state_value1.save()

    # This should be ignored due to versioning.
    feature_state_versioned = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        enabled=True,
        version=100,
    )
    feature_state_value_versioned = feature_state_versioned.feature_state_value
    feature_state_value_versioned.string_value = None
    feature_state_value_versioned.integer_value = 2005
    feature_state_value_versioned.type = INTEGER
    feature_state_value_versioned.save()

    feature_state2 = feature2.feature_states.filter(environment=environment).first()
    feature_state2.enabled = True
    feature_state2.save()

    feature_state_value2 = feature_state2.feature_state_value
    feature_state_value2.string_value = None
    feature_state_value2.boolean_value = True
    feature_state_value2.type = BOOLEAN
    feature_state_value2.save()

    feature_state_value3 = (
        feature3.feature_states.filter(environment=environment)
        .first()
        .feature_state_value
    )
    feature_state_value3.string_value = "present"
    feature_state_value3.save()

    # This should be ignored due to identity being set.
    FeatureState.objects.create(
        feature=feature2,
        environment=environment,
        identity=identity,
    )

    # This should be ignored due to feature segment being set.
    FeatureState.objects.create(
        feature=feature2,
        environment=environment,
        feature_segment=feature_segment,
    )

    # Multivariate should be ignored.
    MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=30,
        type=STRING,
        string_value="mv_feature_option1",
    )
    MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=70,
        type=STRING,
        string_value="mv_feature_option2",
    )

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}"

    # When
    with django_assert_num_queries(16):
        response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 3
    results = response.data["results"]

    assert results[0]["environment_feature_state"]["enabled"] is True
    assert results[0]["environment_feature_state"]["feature_state_value"] == 2005
    assert results[0]["name"] == feature.name
    assert results[1]["environment_feature_state"]["enabled"] is True
    assert results[1]["environment_feature_state"]["feature_state_value"] is True
    assert results[1]["name"] == feature2.name
    assert results[2]["environment_feature_state"]["enabled"] is False
    assert results[2]["environment_feature_state"]["feature_state_value"] == "present"
    assert results[2]["name"] == feature3.name


def test_list_features_with_filter_by_value_search_string_and_int(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature4 = Feature.objects.create(
        name="fancy_feature", project=project, initial_value="fancy"
    )

    Environment.objects.create(
        name="Out of test scope environment",
        project=project,
    )

    feature_state1 = feature.feature_states.filter(environment=environment).first()
    feature_state1.enabled = True
    feature_state1.save()

    feature_state_value1 = feature_state1.feature_state_value
    feature_state_value1.string_value = None
    feature_state_value1.integer_value = 1945
    feature_state_value1.type = INTEGER
    feature_state_value1.save()

    feature_state2 = feature2.feature_states.filter(environment=environment).first()
    feature_state2.enabled = True
    feature_state2.save()

    feature_state_value2 = feature_state2.feature_state_value
    feature_state_value2.string_value = None
    feature_state_value2.boolean_value = True
    feature_state_value2.type = BOOLEAN
    feature_state_value2.save()

    feature_state_value3 = (
        feature3.feature_states.filter(environment=environment)
        .first()
        .feature_state_value
    )
    feature_state_value3.string_value = "present"
    feature_state_value3.type = STRING
    feature_state_value3.save()

    feature_state4 = feature4.feature_states.filter(environment=environment).first()
    feature_state4.enabled = True
    feature_state4.save()

    feature_state_value4 = feature_state4.feature_state_value
    feature_state_value4.string_value = "year 1945"
    feature_state_value4.type = STRING
    feature_state_value4.save()

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}&value_search=1945&is_enabled=true"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Only two features met the criteria.
    assert len(response.data["results"]) == 2
    features = {result["name"] for result in response.data["results"]}
    assert feature.name in features
    assert feature4.name in features


def test_list_features_with_filter_by_search_value_boolean(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature4 = Feature.objects.create(
        name="fancy_feature", project=project, initial_value="fancy"
    )

    Environment.objects.create(
        name="Out of test scope environment",
        project=project,
    )

    feature_state1 = feature.feature_states.filter(environment=environment).first()
    feature_state1.enabled = True
    feature_state1.save()

    feature_state_value1 = feature_state1.feature_state_value
    feature_state_value1.string_value = None
    feature_state_value1.integer_value = 1945
    feature_state_value1.type = INTEGER
    feature_state_value1.save()

    feature_state2 = feature2.feature_states.filter(environment=environment).first()
    feature_state2.enabled = False
    feature_state2.save()

    feature_state_value2 = feature_state2.feature_state_value
    feature_state_value2.string_value = None
    feature_state_value2.boolean_value = True
    feature_state_value2.type = BOOLEAN
    feature_state_value2.save()

    feature_state_value3 = (
        feature3.feature_states.filter(environment=environment)
        .first()
        .feature_state_value
    )
    feature_state_value3.string_value = "present"
    feature_state_value3.type = STRING
    feature_state_value3.save()

    feature_state4 = feature4.feature_states.filter(environment=environment).first()
    feature_state4.enabled = True
    feature_state4.save()

    feature_state_value4 = feature_state4.feature_state_value
    feature_state_value4.string_value = "year 1945"
    feature_state_value4.type = STRING
    feature_state_value4.save()

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}&value_search=true&is_enabled=false"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == feature2.name


def test_simple_feature_state_returns_only_latest_versions(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    # Given
    url = "%s?environment=%d" % (
        reverse("api-v1:features:featurestates-list"),
        environment_v2_versioning.id,
    )

    with_environment_permissions(
        [VIEW_ENVIRONMENT], environment_id=environment_v2_versioning.id
    )

    # Let's create some new versions, with some segment overrides
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    feature_segment_v2 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
    )
    FeatureState.objects.create(
        feature_segment=feature_segment_v2,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
    )
    version_2.publish(staff_user)

    version_3 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    version_3.publish(staff_user)

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 2


@pytest.mark.freeze_time(two_hours_ago)
def test_feature_list_last_modified_values(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    environment_v2_versioning: Environment,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    # another v2 versioning environment
    environment_v2_versioning_2 = Environment.objects.create(
        name="environment 2", project=project, use_v2_feature_versioning=True
    )

    url = "{base_url}?environment={environment_id}".format(
        base_url=reverse("api-v1:projects:project-features-list", args=[project.id]),
        environment_id=environment_v2_versioning.id,
    )

    with_project_permissions([VIEW_PROJECT])

    with freeze_time(one_hour_ago):
        # create a new published version in another environment, simulated to be one hour ago
        environment_v2_versioning_2_version_2 = (
            EnvironmentFeatureVersion.objects.create(
                environment=environment_v2_versioning_2, feature=feature
            )
        )
        environment_v2_versioning_2_version_2.publish(staff_user)

    with freeze_time(now):
        # and create a new unpublished version in the current environment, simulated to be now
        # this shouldn't affect the values returned
        EnvironmentFeatureVersion.objects.create(
            environment=environment_v2_versioning, feature=feature
        )

    # let's add a few more features to ensure we aren't adding N+1 issues
    for i in range(2):
        Feature.objects.create(name=f"feature_{i}", project=project)

    # When
    with django_assert_num_queries(16):  # TODO: reduce this number of queries!
        response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3

    feature_data = next(
        filter(lambda r: r["id"] == feature.id, response_json["results"])
    )
    assert feature_data["last_modified_in_any_environment"] == one_hour_ago.isoformat()
    assert (
        feature_data["last_modified_in_current_environment"]
        == two_hours_ago.isoformat()
    )


def test_filter_features_with_owners(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    admin_user: FFAdminUser,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="included_feature", project=project, initial_value="initial_value"
    )
    Feature.objects.create(
        name="not_included_feature", project=project, initial_value="gone"
    )

    # Include admin only in the first feature.
    feature.owners.add(admin_user)

    # Include staff only in the second feature.
    feature2.owners.add(staff_user)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Search for both users in the owners query param.
    url = (
        f"{base_url}?environment={environment.id}&"
        f"owners={admin_user.id},{staff_user.id}"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == feature.id
    assert response.data["results"][1]["id"] == feature2.id


def test_filter_features_with_group_owners(
    staff_client: APIClient,
    project: Project,
    organisation: Organisation,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="included_feature", project=project, initial_value="initial_value"
    )
    Feature.objects.create(
        name="not_included_feature", project=project, initial_value="gone"
    )

    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Second Group", organisation=organisation
    )

    feature.group_owners.add(group_1)
    feature2.group_owners.add(group_2)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Search for both users in the owners query param.
    url = (
        f"{base_url}?environment={environment.id}&"
        f"group_owners={group_1.id},{group_2.id}"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == feature.id
    assert response.data["results"][1]["id"] == feature2.id


def test_filter_features_with_owners_and_group_owners_together(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    project: Project,
    organisation: Organisation,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="included_feature", project=project, initial_value="initial_value"
    )
    Feature.objects.create(
        name="not_included_feature", project=project, initial_value="gone"
    )

    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )

    feature.group_owners.add(group_1)
    feature2.owners.add(staff_user)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Search for both users in the owners query param.
    url = (
        f"{base_url}?environment={environment.id}&"
        f"group_owners={group_1.id}&owners={staff_user.id}"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == feature.id
    assert response.data["results"][1]["id"] == feature2.id
