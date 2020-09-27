import json
from unittest.case import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from environments.identities.models import Identity
from environments.models import Environment
from environments.identities.traits.models import Trait
from features.models import Feature, FeatureSegment
from features.feature_states.models import FeatureState
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments import models
from segments.models import Segment, SegmentRule, Condition
from util.tests import Helper


@pytest.mark.django_db
class IdentityTestCase(TestCase):
    identifier = "user1"
    put_template = '{ "enabled" : "%r" }'
    post_template = '{ "feature" : "%s", "enabled" : "%r" }'
    feature_states_url = "/api/v1/environments/%s/identities/%s/featurestates/"
    feature_states_detail_url = feature_states_url + "%d/"
    identities_url = "/api/v1/environments/%s/identities/%s/"

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name="Test Org")
        user.add_organisation(
            self.organisation, OrganisationRole.ADMIN
        )  # admin to bypass perms

        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test Environment", project=self.project
        )
        self.identity = Identity.objects.create(
            identifier=self.identifier, environment=self.environment
        )

    def test_should_return_identities_list_when_requested(self):
        # Given - set up data

        # When
        response = self.client.get(
            self.identities_url % (self.identity.environment.api_key, self.identity.id)
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_should_create_identity_feature_when_post(self):
        # Given
        feature = Feature.objects.create(name="feature1", project=self.project)

        # When
        response = self.client.post(
            self.feature_states_url
            % (self.identity.environment.api_key, self.identity.id),
            data=self.post_template % (feature.id, True),
            content_type="application/json",
        )

        # Then
        identity_features = self.identity.identity_features
        assert response.status_code == status.HTTP_201_CREATED
        assert identity_features.count() == 1

    def test_should_return_BadRequest_when_duplicate_identityFeature_is_posted(self):
        # Given
        feature = Feature.objects.create(name="feature2", project=self.project)

        # When
        initial_response = self.client.post(
            self.feature_states_url
            % (self.identity.environment.api_key, self.identity.id),
            data=self.post_template % (feature.id, True),
            content_type="application/json",
        )
        second_response = self.client.post(
            self.feature_states_url
            % (self.identity.environment.api_key, self.identity.id),
            data=self.post_template % (feature.id, True),
            content_type="application/json",
        )

        # Then
        identity_feature = self.identity.identity_features
        assert initial_response.status_code == status.HTTP_201_CREATED
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert identity_feature.count() == 1

    def test_should_change_enabled_state_when_put(self):
        # Given
        feature = Feature.objects.create(name="feature1", project=self.project)
        feature_state = FeatureState.objects.create(
            feature=feature,
            identity=self.identity,
            enabled=False,
            environment=self.environment,
        )

        # When
        response = self.client.put(
            self.feature_states_detail_url
            % (self.identity.environment.api_key, self.identity.id, feature_state.id),
            data=self.put_template % True,
            content_type="application/json",
        )
        feature_state.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert feature_state.enabled == True

    def test_should_remove_identity_feature_when_delete(self):
        # Given
        feature_one = Feature.objects.create(name="feature1", project=self.project)
        feature_two = Feature.objects.create(name="feature2", project=self.project)
        identity_feature_one = FeatureState.objects.create(
            feature=feature_one,
            identity=self.identity,
            enabled=False,
            environment=self.environment,
        )
        identity_feature_two = FeatureState.objects.create(
            feature=feature_two,
            identity=self.identity,
            enabled=True,
            environment=self.environment,
        )

        # When
        self.client.delete(
            self.feature_states_detail_url
            % (
                self.identity.environment.api_key,
                self.identity.id,
                identity_feature_one.id,
            ),
            content_type="application/json",
        )

        # Then
        identity_features = FeatureState.objects.filter(identity=self.identity)
        assert identity_features.count() == 1

    def test_can_search_for_identities(self):
        # Given
        Identity.objects.create(identifier="user2", environment=self.environment)
        base_url = reverse(
            "api-v1:environments:environment-identities-list",
            args=[self.environment.api_key],
        )
        url = "%s?q=%s" % (base_url, self.identifier)

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and - only identity matching search appears
        assert res.json().get("count") == 1

    def test_search_is_case_insensitive(self):
        # Given
        Identity.objects.create(identifier="user2", environment=self.environment)
        base_url = reverse(
            "api-v1:environments:environment-identities-list",
            args=[self.environment.api_key],
        )
        url = "%s?q=%s" % (base_url, self.identifier.upper())

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and - identity matching search appears
        assert res.json().get("count") == 1

    def test_no_identities_returned_if_search_matches_none(self):
        # Given
        base_url = reverse(
            "api-v1:environments:environment-identities-list",
            args=[self.environment.api_key],
        )
        url = "%s?q=%s" % (base_url, "some invalid search string")

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert res.json().get("count") == 0

    def test_search_identities_still_allows_paging(self):
        # Given
        self._create_n_identities(10)
        base_url = reverse(
            "api-v1:environments:environment-identities-list",
            args=[self.environment.api_key],
        )
        url = "%s?q=%s" % (base_url, "user")

        res1 = self.client.get(url)
        second_page = res1.json().get("next")

        # When
        res2 = self.client.get(second_page)

        # Then
        assert res2.status_code == status.HTTP_200_OK

        # and
        assert res2.json().get("results")

    def _create_n_identities(self, n):
        for i in range(2, n + 2):
            identifier = "user%d" % i
            Identity.objects.create(identifier=identifier, environment=self.environment)

    def test_can_delete_identity(self):
        # Given
        url = reverse(
            "api-v1:environments:environment-identities-detail",
            args=[self.environment.api_key, self.identity.id],
        )

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert not Identity.objects.filter(id=self.identity.id).exists()


@pytest.mark.django_db
class SDKIdentitiesTestCase(APITestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(
            organisation=self.organisation, name="Test Project"
        )
        self.environment = Environment.objects.create(
            project=self.project, name="Test Environment"
        )
        self.feature_1 = Feature.objects.create(
            project=self.project, name="Test Feature 1"
        )
        self.feature_2 = Feature.objects.create(
            project=self.project, name="Test Feature 2"
        )
        self.identity = Identity.objects.create(
            environment=self.environment, identifier="test-identity"
        )
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)

    def tearDown(self) -> None:
        Segment.objects.all().delete()

    def test_identities_endpoint_returns_all_feature_states_for_identity_if_feature_not_provided(
        self,
    ):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert len(response.json().get("flags")) == 2

    def test_identities_endpoint_returns_traits(self):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier
        trait = Trait.objects.create(
            identity=self.identity,
            trait_key="trait_key",
            value_type="STRING",
            string_value="trait_value",
        )

        # When
        response = self.client.get(url)

        # Then
        assert response.json().get("traits") is not None

        # and
        assert (
            response.json().get("traits")[0].get("trait_value")
            == trait.get_trait_value()
        )

    def test_identities_endpoint_returns_single_feature_state_if_feature_provided(self):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = (
            base_url
            + "?identifier="
            + self.identity.identifier
            + "&feature="
            + self.feature_1.name
        )

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert response.json().get("feature").get("name") == self.feature_1.name

    def test_identities_endpoint_returns_value_for_segment_if_identity_in_segment(self):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier

        trait_key = "trait_key"
        trait_value = "trait_value"
        Trait.objects.create(
            identity=self.identity,
            trait_key=trait_key,
            value_type="STRING",
            string_value=trait_value,
        )
        segment = Segment.objects.create(name="Test Segment", project=self.project)
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            operator="EQUAL", property=trait_key, value=trait_value, rule=segment_rule
        )
        FeatureSegment.objects.create(
            segment=segment,
            feature=self.feature_2,
            environment=self.environment,
            enabled=True,
            priority=1,
        )

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert response.json().get("flags")[1].get("enabled")

    def test_identities_endpoint_returns_value_for_segment_if_identity_in_segment_and_feature_specified(
        self,
    ):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = (
            base_url
            + "?identifier="
            + self.identity.identifier
            + "&feature="
            + self.feature_1.name
        )

        trait_key = "trait_key"
        trait_value = "trait_value"
        Trait.objects.create(
            identity=self.identity,
            trait_key=trait_key,
            value_type="STRING",
            string_value=trait_value,
        )
        segment = Segment.objects.create(name="Test Segment", project=self.project)
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            operator="EQUAL", property=trait_key, value=trait_value, rule=segment_rule
        )
        FeatureSegment.objects.create(
            segment=segment,
            feature=self.feature_1,
            environment=self.environment,
            enabled=True,
            priority=1,
        )

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert response.json().get("enabled")

    def test_identities_endpoint_returns_value_for_segment_if_rule_type_percentage_split_and_identity_in_segment(
        self,
    ):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier

        segment = Segment.objects.create(name="Test Segment", project=self.project)
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )

        identity_percentage_value = segment.get_identity_percentage_value(self.identity)
        Condition.objects.create(
            operator=models.PERCENTAGE_SPLIT,
            value=(identity_percentage_value + (1 - identity_percentage_value) / 2)
            * 100.0,
            rule=segment_rule,
        )
        FeatureSegment.objects.create(
            segment=segment,
            feature=self.feature_1,
            environment=self.environment,
            enabled=True,
            priority=1,
        )

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        for flag in response.json()["flags"]:
            if flag["feature"]["name"] == self.feature_1.name:
                assert flag["enabled"]

    def test_identities_endpoint_returns_default_value_if_rule_type_percentage_split_and_identity_not_in_segment(
        self,
    ):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier

        segment = Segment.objects.create(name="Test Segment", project=self.project)
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )

        identity_percentage_value = segment.get_identity_percentage_value(self.identity)
        Condition.objects.create(
            operator=models.PERCENTAGE_SPLIT,
            value=identity_percentage_value / 2,
            rule=segment_rule,
        )
        FeatureSegment.objects.create(
            segment=segment,
            feature=self.feature_1,
            environment=self.environment,
            enabled=True,
            priority=1,
        )

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert not response.json().get("flags")[0].get("enabled")

    def test_post_identify_with_persistence(self):
        # Given
        url = reverse("api-v1:sdk-identities")

        # a payload for an identity with 2 traits
        data = {
            "identifier": self.identity.identifier,
            "traits": [
                {"trait_key": "my_trait", "trait_value": 123},
                {"trait_key": "my_other_trait", "trait_value": "a value"},
            ],
        }

        # When
        # we identify that user by posting the above payload
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        # we get everything we expect in the response
        response_json = response.json()
        assert response_json["flags"]
        assert response_json["traits"]

        # and the traits ARE persisted
        assert self.identity.identity_traits.count() == 2

    def test_post_identify_without_persistence(self):
        # Given
        url = reverse("api-v1:sdk-identities")

        # an organisation configured to not persist traits
        self.organisation.persist_trait_data = False
        self.organisation.save()

        # and a payload for an identity with 2 traits
        data = {
            "identifier": self.identity.identifier,
            "traits": [
                {"trait_key": "my_trait", "trait_value": 123},
                {"trait_key": "my_other_trait", "trait_value": "a value"},
            ],
        }

        # When
        # we identify that user by posting the above payload
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        # we get everything we expect in the response
        response_json = response.json()
        assert response_json["flags"]
        assert response_json["traits"]

        # and the traits ARE NOT persisted
        assert self.identity.identity_traits.count() == 0
