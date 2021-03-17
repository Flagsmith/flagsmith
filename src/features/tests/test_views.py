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
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment
from users.models import FFAdminUser
from util.tests import Helper

# patch this function as it's triggering extra threads and causing errors
mock.patch("features.models.trigger_feature_state_change_webhooks").start()


@pytest.mark.django_db
class ProjectFeatureTestCase(TestCase):
    project_features_url = "/api/v1/projects/%s/features/"
    project_feature_detail_url = "/api/v1/projects/%s/features/%d/"
    post_template = '{ "name": "%s", "project": %d, "initial_value": "%s" }'

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name="Test Org")

        user.add_organisation(self.organisation, OrganisationRole.ADMIN)

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

    def test_should_create_feature_states_when_feature_created(self):
        # Given - set up data
        default_value = "This is a value"
        data = {
            "name": "test feature",
            "initial_value": default_value,
            "project": self.project.id,
        }
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        # check feature was created successfully
        assert (
            Feature.objects.filter(name="test feature", project=self.project.id).count()
            == 1
        )

        # check feature was added to environment
        assert FeatureState.objects.filter(environment=self.environment_1).count() == 1
        assert FeatureState.objects.filter(environment=self.environment_2).count() == 1

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.filter(
            environment=self.environment_1
        ).first()
        assert feature_state.get_feature_state_value() == default_value

    def test_should_create_feature_states_with_integer_value_when_feature_created(self):
        # Given - set up data
        default_value = 12
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])
        data = {
            "name": "test feature",
            "initial_value": default_value,
            "project": self.project.id,
        }

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        # check feature was created successfully
        assert (
            Feature.objects.filter(name="test feature", project=self.project.id).count()
            == 1
        )

        # check feature was added to environment
        assert FeatureState.objects.filter(environment=self.environment_1).count() == 1
        assert FeatureState.objects.filter(environment=self.environment_2).count() == 1

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.filter(
            environment=self.environment_1
        ).first()
        assert feature_state.get_feature_state_value() == default_value

    def test_should_create_feature_states_with_boolean_value_when_feature_created(self):
        # Given - set up data
        default_value = True
        feature_name = "Test feature"
        data = {
            "name": "Test feature",
            "initial_value": default_value,
            "project": self.project.id,
        }
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        # check feature was created successfully
        assert (
            Feature.objects.filter(name=feature_name, project=self.project.id).count()
            == 1
        )

        # check feature was added to environment
        assert FeatureState.objects.filter(environment=self.environment_1).count() == 1
        assert FeatureState.objects.filter(environment=self.environment_2).count() == 1

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.filter(
            environment=self.environment_1
        ).first()
        assert feature_state.get_feature_state_value() == default_value

    def test_should_delete_feature_states_when_feature_deleted(self):
        # Given
        feature = Feature.objects.create(name="test feature", project=self.project)

        # When
        response = self.client.delete(
            self.project_feature_detail_url % (self.project.id, feature.id)
        )

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # check feature was deleted successfully
        assert (
            Feature.objects.filter(name="test feature", project=self.project.id).count()
            == 0
        )

        # check feature was removed from all environments
        assert (
            FeatureState.objects.filter(
                environment=self.environment_1, feature=feature
            ).count()
            == 0
        )
        assert (
            FeatureState.objects.filter(
                environment=self.environment_2, feature=feature
            ).count()
            == 0
        )

    def test_audit_log_created_when_feature_created(self):
        # Given
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])
        data = {"name": "Test feature flag", "type": "FLAG", "project": self.project.id}

        # When
        self.client.post(url, data=data)

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.FEATURE.name
            ).count()
            == 1
        )

    def test_audit_log_created_when_feature_updated(self):
        # Given
        feature = Feature.objects.create(name="Test Feature", project=self.project)
        url = reverse(
            "api-v1:projects:project-features-detail",
            args=[self.project.id, feature.id],
        )
        data = {
            "name": "Test Feature updated",
            "type": "FLAG",
            "project": self.project.id,
        }

        # When
        self.client.put(url, data=data)

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.FEATURE.name
            ).count()
            == 1
        )

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
        res = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )

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
        res = self.client.delete(url)

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

    def test_should_create_tags_when_feature_created(self):
        # Given - set up data
        default_value = "Test"
        feature_name = "Test feature"
        data = {
            "name": feature_name,
            "project": self.project.id,
            "initial_value": default_value,
            "tags": [self.tag_one.id, self.tag_two.id],
        }

        # When
        response = self.client.post(
            self.project_features_url % self.project.id,
            data=json.dumps(data),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        # check feature was created successfully
        feature = Feature.objects.filter(
            name=feature_name, project=self.project.id
        ).first()

        # check tags where added
        assert feature.tags.count() == 2
        self.assertEqual(list(feature.tags.all()), [self.tag_one, self.tag_two])

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

    def test_list_features_return_tags(self):
        # Given
        Feature.objects.create(name="test_feature", project=self.project)
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()
        assert response_json["count"] == 1

        feature = response_json["results"][0]
        assert "tags" in feature

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
        )


@pytest.mark.django_db()
class FeatureStateViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            project=self.project, name="Test environment"
        )
        self.feature = Feature.objects.create(
            name="test-feature", project=self.project, type="CONFIG", initial_value=12
        )
        self.user = FFAdminUser.objects.create(email="test@example.com")
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_update_feature_state_value_updates_feature_state_value(self):
        # Given
        feature_state = FeatureState.objects.get(
            environment=self.environment, feature=self.feature
        )
        url = reverse(
            "api-v1:environments:environment-featurestates-detail",
            args=[self.environment.api_key, feature_state.id],
        )
        new_value = "new-value"
        data = {
            "id": feature_state.id,
            "feature_state_value": new_value,
            "enabled": False,
            "feature": self.feature.id,
            "environment": self.environment.id,
            "identity": None,
            "feature_segment": None,
        }

        # When
        self.client.put(url, data=json.dumps(data), content_type="application/json")

        # Then
        feature_state.refresh_from_db()
        assert feature_state.get_feature_state_value() == new_value

    def test_can_filter_feature_states_to_show_identity_overrides_only(self):
        # Given
        feature_state = FeatureState.objects.get(
            environment=self.environment, feature=self.feature
        )

        identifier = "test-identity"
        identity = Identity.objects.create(
            identifier=identifier, environment=self.environment
        )
        identity_feature_state = FeatureState.objects.create(
            environment=self.environment, feature=self.feature, identity=identity
        )

        base_url = reverse(
            "api-v1:environments:environment-featurestates-list",
            args=[self.environment.api_key],
        )
        url = base_url + "?anyIdentity&feature=" + str(self.feature.id)

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert len(res.json().get("results")) == 1

        # and
        assert res.json()["results"][0]["identity"]["identifier"] == identifier


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


@pytest.mark.django_db
class SimpleFeatureStateViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.user = FFAdminUser.objects.create(email="test@example.com")
        self.organisation = Organisation.objects.create(name="Test organisation")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.feature = Feature.objects.create(name="test_feature", project=self.project)
        self.environment = Environment.objects.create(
            name="Test environment", project=self.project
        )

        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_feature_state(self):
        # Given
        # To create a feature state, it needs to be for a feature segment or an identity
        identity = Identity.objects.create(
            identifier="identifier", environment=self.environment
        )
        create_url = reverse("api-v1:features:featurestates-list")
        data = {
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "test value"},
            "identity": identity.id,
            "environment": self.environment.id,
            "feature": self.feature.id,
        }

        # When
        response = self.client.post(
            create_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_feature_states_for_environment(self):
        # Given - another environment
        Environment.objects.create(name="Another environment", project=self.project)
        base_url = reverse("api-v1:features:featurestates-list")
        url = f"{base_url}?environment={self.environment.id}"

        # When - we list the feature statues for on environment
        response = self.client.get(url)

        # Then - we only get one feature state back
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()
        assert response_json["count"] == 1
        assert response_json["results"][0]["environment"] == self.environment.id
