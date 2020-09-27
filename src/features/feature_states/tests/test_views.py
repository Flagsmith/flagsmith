import json
from unittest.case import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from environments.identities.models import Identity
from environments.models import Environment
from features.constants import CONFIG
from features.feature_states.models import FeatureState, FeatureStateValue
from features.models import Feature, FeatureSegment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser


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
            type=CONFIG,
            initial_value=self.environment_fs_value,
        )
        segment = Segment.objects.create(name="Test segment", project=self.project)
        FeatureSegment.objects.create(
            segment=segment,
            feature=self.feature,
            value=self.segment_fs_value,
            environment=self.environment,
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
        config_flag = Feature.objects.create(
            name="Config", project=project_flag_disabled, type=CONFIG
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
        assert len(response_json) == 2

        # disabled flags are not returned
        for flag in response_json:
            assert flag["feature"]["id"] != disabled_flag.id

        # And
        # but enabled ones and remote configs are
        assert response_json[0]["feature"]["id"] == config_flag.id
        assert response_json[1]["feature"]["id"] == enabled_flag.id
