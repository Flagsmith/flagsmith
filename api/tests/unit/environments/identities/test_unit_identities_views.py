import json
import urllib
from unittest import mock

from core.constants import FLAGSMITH_UPDATED_AT_HEADER, STRING
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from pytest_django import DjangoAssertNumQueries
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from environments.identities.helpers import (
    get_hashed_percentage_for_object_ids,
)
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.identities.views import IdentityViewSet
from environments.models import Environment, EnvironmentAPIKey
from environments.permissions.constants import (
    MANAGE_IDENTITIES,
    VIEW_IDENTITIES,
)
from environments.permissions.permissions import NestedEnvironmentPermissions
from features.models import Feature, FeatureSegment, FeatureState
from integrations.amplitude.models import AmplitudeConfiguration
from organisations.models import Organisation
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule


def test_should_return_identities_list_when_requested(
    environment: Environment,
    identity: Identity,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-identities-detail",
        args=[environment.api_key, identity.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["environment"] == environment.id
    assert response.data["id"] == identity.id
    assert response.data["identifier"] == identity.identifier


def test_should_create_identity_feature_when_post(
    feature: Feature,
    admin_client: APIClient,
    identity: Identity,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=[identity.environment.api_key, identity.id],
    )

    # When
    response = admin_client.post(
        url,
        data=json.dumps({"feature": feature.id, "enabled": True}),
        content_type="application/json",
    )

    # Then
    identity_features = identity.identity_features
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["feature"] == feature.id
    assert response.data["identity"] == identity.id
    assert identity_features.count() == 1


def test_should_return_400_when_duplicate_identity_feature_is_posted(
    feature: Feature,
    admin_client: APIClient,
    identity: Identity,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=[identity.environment.api_key, identity.id],
    )

    # When
    initial_response = admin_client.post(
        url,
        data=json.dumps({"feature": feature.id, "enabled": True}),
        content_type="application/json",
    )
    second_response = admin_client.post(
        url,
        data=json.dumps({"feature": feature.id, "enabled": True}),
        content_type="application/json",
    )

    # Then
    assert initial_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_400_BAD_REQUEST
    identity_feature = identity.identity_features
    assert identity_feature.count() == 1


def test_should_change_enabled_state_when_put(
    feature: Feature,
    admin_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        feature=feature,
        identity=identity,
        enabled=False,
        environment=environment,
    )

    url = reverse(
        "api-v1:environments:identity-featurestates-detail",
        args=[environment.api_key, identity.id, feature_state.id],
    )
    # When
    response = admin_client.put(
        url,
        data=json.dumps({"enabled": True}),
        content_type="application/json",
    )
    feature_state.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert feature_state.enabled


def test_should_remove_identity_feature_when_delete(
    admin_client: APIClient,
    feature: Feature,
    project: Project,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    feature2 = Feature.objects.create(name="feature2", project=project)
    identity_feature1 = FeatureState.objects.create(
        feature=feature,
        identity=identity,
        enabled=False,
        environment=environment,
    )
    FeatureState.objects.create(
        feature=feature2,
        identity=identity,
        enabled=True,
        environment=environment,
    )

    url = reverse(
        "api-v1:environments:identity-featurestates-detail",
        args=[environment.api_key, identity.id, identity_feature1.id],
    )

    # When
    admin_client.delete(url, content_type="application/json")

    # Then
    identity_features = FeatureState.objects.filter(identity=identity)
    assert identity_features.count() == 1


def test_can_search_for_identities(
    admin_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment.api_key],
    )
    url = f"{base_url}?q={identity.identifier}"

    # Identity for non-inclusion.
    Identity.objects.create(identifier="identifier2", environment=environment)

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Only identity matching search appears.
    assert response.data["count"] == 1
    assert response.data["results"][0]["identifier"] == identity.identifier


def test_can_search_for_identities_with_exact_match(
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    # Note that the idenifiers all have the number 1, but only the
    # exact match will be returned due to the quotes in the query.
    identity_to_return = Identity.objects.create(
        identifier="1", environment=environment
    )
    Identity.objects.create(identifier="12", environment=environment)
    Identity.objects.create(identifier="121", environment=environment)
    base_url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment.api_key],
    )
    path_encoded = urllib.parse.urlencode({"q": '"1"'})
    url = f"{base_url}?{path_encoded}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Only identity matching search appears
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == identity_to_return.id


def test_search_identities_is_case_insensitive(
    identity: Identity,
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment.api_key],
    )
    assert identity.identifier != identity.identifier.upper()
    url = f"{base_url}?q={identity.identifier.upper()}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # and - identity matching search appears
    assert response.data["count"] == 1


def test_no_identities_returned_if_search_matches_none(
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment.api_key],
    )
    url = "%s?q=%s" % (base_url, "some invalid search string")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0


def test_search_identities_still_allows_paging(
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    for i in range(12):
        identifier = f"user.{i}"
        Identity.objects.create(identifier=identifier, environment=environment)
    base_url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment.api_key],
    )
    url = f"{base_url}?q=user&page_size=10"

    response1 = admin_client.get(url)
    second_page = response1.data["next"]

    # When
    response2 = admin_client.get(second_page)

    # Then
    assert response2.status_code == status.HTTP_200_OK
    assert response2.data["results"]


def test_can_delete_identity(
    environment: Environment,
    admin_client: APIClient,
    identity: Identity,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-identities-detail",
        args=[environment.api_key, identity.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Identity.objects.filter(id=identity.id).exists()


def test_identities_endpoint_returns_all_feature_states_for_identity_if_feature_not_provided(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
) -> None:
    # Given
    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    Feature.objects.create(project=environment.project, name="Test Feature 1")
    Feature.objects.create(project=environment.project, name="Test Feature 2")

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["flags"]) == 2


@mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
def test_identities_endpoint_get_all_feature_amplitude_called(
    mock_amplitude_wrapper: mock.MagicMock,
    environment: Environment,
    identity: Identity,
    api_client: APIClient,
) -> None:
    # Given
    # amplitude configuration for environment
    AmplitudeConfiguration.objects.create(api_key="abc-123", environment=environment)
    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    Feature.objects.create(project=environment.project, name="Test Feature 1")
    Feature.objects.create(project=environment.project, name="Test Feature 2")

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["flags"]) == 2

    # and amplitude identify users should be called
    mock_amplitude_wrapper.assert_called()


@mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
def test_identities_endpoint_returns_traits(
    mock_amplitude_wrapper: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    trait = Trait.objects.create(
        identity=identity,
        trait_key="trait_key",
        value_type=STRING,
        string_value="trait_value",
    )
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier

    # When
    response = api_client.get(url)

    # Then
    assert response.data["traits"] is not None
    assert response.data["traits"][0].get("trait_value") == trait.get_trait_value()

    # and amplitude identify users should not be called
    mock_amplitude_wrapper.assert_not_called()


def test_identities_endpoint_returns_single_feature_state_if_feature_provided(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
) -> None:
    # Given
    feature_1 = Feature.objects.create(
        project=environment.project, name="Test Feature 1"
    )
    Feature.objects.create(project=environment.project, name="Test Feature 2")

    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity.identifier}&feature={feature_1.name}"

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["feature"]["name"] == feature_1.name


@mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
def test_identities_endpoint_returns_value_for_segment_if_identity_in_segment(
    mock_amplitude_wrapper: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    trait_key = "trait_key"
    trait_value = "trait_value"
    Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        operator="EQUAL", property=trait_key, value=trait_value, rule=segment_rule
    )
    Feature.objects.create(project=environment.project, name="Test Feature 1")
    feature_2 = Feature.objects.create(
        project=environment.project, name="Test Feature 2"
    )

    feature_segment = FeatureSegment.objects.create(
        segment=segment,
        feature=feature_2,
        environment=environment,
        priority=1,
    )
    FeatureState.objects.create(
        feature=feature_2,
        feature_segment=feature_segment,
        environment=environment,
        enabled=True,
    )
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["flags"][1]["enabled"] is True

    # and amplitude identify users should not be called
    mock_amplitude_wrapper.assert_not_called()


@mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
def test_identities_endpoint_returns_value_for_segment_if_identity_in_segment_and_feature_specified(
    mock_amplitude_wrapper: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    trait_key = "trait_key"
    trait_value = "trait_value"
    Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        operator="EQUAL", property=trait_key, value=trait_value, rule=segment_rule
    )
    feature_1 = Feature.objects.create(
        project=environment.project, name="Test Feature 1"
    )
    Feature.objects.create(project=environment.project, name="Test Feature 2")

    feature_segment = FeatureSegment.objects.create(
        segment=segment,
        feature=feature_1,
        environment=environment,
        priority=1,
    )
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature_1,
        environment=environment,
        enabled=True,
    )
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity.identifier}&feature={feature_1.name}"

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["enabled"] is True

    # and amplitude identify users should not be called
    mock_amplitude_wrapper.assert_not_called()


@mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
def test_identities_endpoint_returns_value_for_segment_if_rule_type_percentage_split_and_identity_in_segment(
    mock_amplitude_wrapper: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
    segment: Segment,
    feature: Feature,
) -> None:
    # Given
    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier

    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    identity_percentage_value = get_hashed_percentage_for_object_ids(
        [segment.id, identity.id]
    )
    Condition.objects.create(
        operator=PERCENTAGE_SPLIT,
        value=(identity_percentage_value + (1 - identity_percentage_value) / 2) * 100.0,
        rule=segment_rule,
    )
    feature_segment = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment,
        priority=1,
    )
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        enabled=True,
    )

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    for flag in response.json()["flags"]:
        if flag["feature"]["name"] == feature.name:
            assert flag["enabled"]

    # and amplitude identify users should not be called
    mock_amplitude_wrapper.assert_not_called()


@mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
def test_identities_endpoint_returns_default_value_if_rule_type_percentage_split_and_identity_not_in_segment(
    mock_amplitude_wrapper: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
    segment: Segment,
    feature: Feature,
) -> None:
    # Given
    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier

    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    identity_percentage_value = get_hashed_percentage_for_object_ids(
        [segment.id, identity.id]
    )
    Condition.objects.create(
        operator=PERCENTAGE_SPLIT,
        value=identity_percentage_value / 2,
        rule=segment_rule,
    )
    feature_segment = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment,
        priority=1,
    )
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        enabled=True,
    )

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    assert not response.json().get("flags")[0].get("enabled")

    # and amplitude identify users should not be called
    mock_amplitude_wrapper.assert_not_called()


def test_post_identify_with_new_identity_work_with_null_trait_value(
    environment: Environment,
    api_client: APIClient,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")
    data = {
        "identifier": "new_identity",
        "traits": [
            {"trait_key": "trait_that_does_not_exists", "trait_value": None},
        ],
    }

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert identity.identity_traits.count() == 0


def test_post_identify_deletes_a_trait_if_trait_value_is_none(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
):
    # Given
    url = reverse("api-v1:sdk-identities")
    trait_1 = Trait.objects.create(
        identity=identity,
        trait_key="trait_key_1",
        value_type=STRING,
        string_value="trait_value",
    )
    trait_2 = Trait.objects.create(
        identity=identity,
        trait_key="trait_key_2",
        value_type=STRING,
        string_value="trait_value",
    )

    data = {
        "identifier": identity.identifier,
        "traits": [
            {"trait_key": trait_1.trait_key, "trait_value": None},
            {"trait_key": "trait_that_does_not_exists", "trait_value": None},
        ],
    }

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert identity.identity_traits.count() == 1
    assert identity.identity_traits.filter(trait_key=trait_2.trait_key).exists()


def test_post_identify_with_persistence(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    # A payload for an identity with 2 traits.
    data = {
        "identifier": identity.identifier,
        "traits": [
            {"trait_key": "my_trait", "trait_value": 123},
            {"trait_key": "my_other_trait", "trait_value": "a value"},
        ],
    }

    # When
    # We identify that user by posting the above payload.
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # We get everything we expect in the response.
    response_json = response.json()
    assert response_json["flags"]
    assert response_json["traits"]
    assert identity.identity_traits.count() == 2


def test_post_identify_without_persistence(
    organisation: Organisation,
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    # an organisation configured to not persist traits
    organisation.persist_trait_data = False
    organisation.save()

    # and a payload for an identity with 2 traits
    data = {
        "identifier": identity.identifier,
        "traits": [
            {"trait_key": "my_trait", "trait_value": 123},
            {"trait_key": "my_other_trait", "trait_value": "a value"},
        ],
    }

    # When
    # we identify that user by posting the above payload
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # we get everything we expect in the response
    response_json = response.json()
    assert response_json["flags"]
    assert response_json["traits"]

    # and the traits ARE NOT persisted
    assert identity.identity_traits.count() == 0


@override_settings(EDGE_API_URL="http://localhost")
@mock.patch("environments.identities.views.forward_identity_request")
def test_post_identities_calls_forward_identity_request_with_correct_arguments(
    mocked_forward_identity_request: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    project.enable_dynamo_db = True
    project.save()

    data = {
        "identifier": identity.identifier,
        "traits": [
            {"trait_key": "my_trait", "trait_value": 123},
            {"trait_key": "my_other_trait", "trait_value": "a value"},
        ],
    }

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    api_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    args, kwargs = mocked_forward_identity_request.delay.call_args_list[0]
    assert args == ()
    assert kwargs["args"][0] == "POST"
    assert kwargs["args"][1].get("X-Environment-Key") == environment.api_key
    assert kwargs["args"][2] == environment.project.id

    assert kwargs["kwargs"]["request_data"] == data


@override_settings(EDGE_API_URL="http://localhost")
@mock.patch("environments.identities.views.forward_identity_request")
def test_get_identities_calls_forward_identity_request_with_correct_arguments(
    mocked_forward_identity_request: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    base_url = reverse("api-v1:sdk-identities")
    url = base_url + "?identifier=" + identity.identifier

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    api_client.get(url)

    # Then
    args, kwargs = mocked_forward_identity_request.delay.call_args_list[0]
    assert args == ()
    assert kwargs["args"][0] == "GET"
    assert kwargs["args"][1].get("X-Environment-Key") == environment.api_key
    assert kwargs["args"][2] == project.id

    assert kwargs["kwargs"]["query_params"] == {"identifier": identity.identifier}


def test_post_identities_with_traits_fails_if_client_cannot_set_traits(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")
    data = {
        "identifier": identity.identifier,
        "traits": [{"trait_key": "foo", "trait_value": "bar"}],
    }

    environment.allow_client_traits = False
    environment.save()

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert Trait.objects.count() == 0
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_post_identities_with_traits_success_if_client_cannot_set_traits_server_key(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")
    trait_key, trait_value = "foo", "bar"
    data = {
        "identifier": identity.identifier,
        "traits": [{"trait_key": trait_key, "trait_value": trait_value}],
    }

    environment_api_key = EnvironmentAPIKey.objects.create(environment=environment)

    environment.allow_client_traits = False
    environment.save()
    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert Trait.objects.count() == 1
    trait = Trait.objects.first()
    assert trait.trait_key == trait_key
    assert trait.trait_value == trait_value


def test_post_identities_request_includes_updated_at_header(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")
    data = {
        "identifier": identity.identifier,
        "traits": [{"trait_key": "foo", "trait_value": "bar"}],
    }

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.headers[FLAGSMITH_UPDATED_AT_HEADER] == str(
        environment.updated_at.timestamp()
    )


def test_get_identities_request_includes_updated_at_header(
    environment: Environment,
    api_client: APIClient,
) -> None:
    # Given
    url = "%s?identifier=identifier" % reverse("api-v1:sdk-identities")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.headers[FLAGSMITH_UPDATED_AT_HEADER] == str(
        environment.updated_at.timestamp()
    )


def test_get_identities_nplus1(
    identity: Identity,
    environment: Environment,
    api_client: APIClient,
    feature: Feature,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    """
    Specific test to reproduce N+1 issue found after deployment of
    v2 feature versioning.
    """

    url = "%s?identifier=%s" % (
        reverse("api-v1:sdk-identities"),
        identity.identifier,
    )

    # Let's get a baseline with only a single version of a flag.
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    with django_assert_num_queries(6):
        api_client.get(url)

    # Now let's create some new versions of the same flag
    # and verify that the query count doesn't increase.
    v1_flag = FeatureState.objects.get(environment=environment, feature=feature)
    now = timezone.now()
    for i in range(2, 13):
        v1_flag.clone(env=environment, version=i, live_from=now)

    # Now it is lower.
    with django_assert_num_queries(5):
        api_client.get(url)


def test_get_identities_with_hide_sensitive_data_with_feature_name(
    environment, feature, identity, api_client
):
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    environment.hide_sensitive_data = True
    environment.save()
    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity.identifier}&feature={feature.name}"
    feature_sensitive_fields = [
        "created_date",
        "description",
        "initial_value",
        "default_enabled",
    ]
    fs_sensitive_fields = ["id", "environment", "identity", "feature_segment"]

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    flag = response.json()

    # Check that the sensitive fields are None
    for field in fs_sensitive_fields:
        assert flag[field] is None

    for field in feature_sensitive_fields:
        assert flag["feature"][field] is None


def test_get_identities_with_hide_sensitive_data(
    environment, feature, identity, api_client
):
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    environment.hide_sensitive_data = True
    environment.save()
    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity.identifier}"
    feature_sensitive_fields = [
        "created_date",
        "description",
        "initial_value",
        "default_enabled",
    ]
    fs_sensitive_fields = ["id", "environment", "identity", "feature_segment"]

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Check that the scalar sensitive fields are None
    for flag in response.json()["flags"]:
        for field in fs_sensitive_fields:
            assert flag[field] is None

        for field in feature_sensitive_fields:
            assert flag["feature"][field] is None

    assert response.json()["traits"] == []


def test_post_identities_with_hide_sensitive_data(
    environment, feature, identity, api_client
):
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    environment.hide_sensitive_data = True
    environment.save()
    url = reverse("api-v1:sdk-identities")
    data = {
        "identifier": identity.identifier,
        "traits": [{"trait_key": "foo", "trait_value": "bar"}],
    }
    feature_sensitive_fields = [
        "created_date",
        "description",
        "initial_value",
        "default_enabled",
    ]
    fs_sensitive_fields = ["id", "environment", "identity", "feature_segment"]

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Check that the scalar sensitive fields are None
    for flag in response.json()["flags"]:
        for field in fs_sensitive_fields:
            assert flag[field] is None

        for field in feature_sensitive_fields:
            assert flag["feature"][field] is None

    assert response.json()["traits"] == []


def test_post_identities__server_key_only_feature__return_expected(
    environment: Environment,
    feature: Feature,
    identity: Identity,
    api_client: APIClient,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature.is_server_key_only = True
    feature.save()

    url = reverse("api-v1:sdk-identities")
    data = {
        "identifier": identity.identifier,
        "traits": [{"trait_key": "foo", "trait_value": "bar"}],
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not response.json()["flags"]


def test_post_identities__server_key_only_feature__server_key_auth__return_expected(
    environment_api_key: EnvironmentAPIKey,
    feature: Feature,
    identity: Identity,
    api_client: APIClient,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)
    feature.is_server_key_only = True
    feature.save()

    url = reverse("api-v1:sdk-identities")
    data = {
        "identifier": identity.identifier,
        "traits": [{"trait_key": "foo", "trait_value": "bar"}],
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["flags"]


def test_user_with_view_identities_permission_can_retrieve_identity(
    environment,
    identity,
    test_user_client,
    view_environment_permission,
    view_identities_permission,
    view_project_permission,
    user_environment_permission,
    user_project_permission,
):
    # Given

    user_environment_permission.permissions.add(
        view_environment_permission, view_identities_permission
    )
    user_project_permission.permissions.add(view_project_permission)

    url = reverse(
        "api-v1:environments:environment-identities-detail",
        args=(environment.api_key, identity.id),
    )

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_user_with_view_environment_permission_can_not_list_identities(
    environment,
    identity,
    test_user_client,
    view_environment_permission,
    manage_identities_permission,
    view_project_permission,
    user_environment_permission,
    user_project_permission,
):
    # Given

    user_environment_permission.permissions.add(view_environment_permission)
    user_project_permission.permissions.add(view_project_permission)

    url = reverse(
        "api-v1:environments:environment-identities-list",
        args=(environment.api_key,),
    )

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_identity_view_set_get_permissions():
    # Given
    view_set = IdentityViewSet()

    # When
    permissions = view_set.get_permissions()

    # Then
    assert isinstance(permissions[0], IsAuthenticated)
    assert isinstance(permissions[1], NestedEnvironmentPermissions)

    assert permissions[1].action_permission_map == {
        "list": VIEW_IDENTITIES,
        "retrieve": VIEW_IDENTITIES,
        "create": MANAGE_IDENTITIES,
        "update": MANAGE_IDENTITIES,
        "partial_update": MANAGE_IDENTITIES,
        "destroy": MANAGE_IDENTITIES,
    }
