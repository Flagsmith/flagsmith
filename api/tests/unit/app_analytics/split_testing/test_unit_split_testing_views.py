import json
from typing import Callable

from app_analytics.split_testing.models import SplitTest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from projects.models import Project


def test_conversion_event(
    api_client: APIClient,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:conversion-events-list")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    data = {"identity_identifier": identity.identifier}

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == data


def test_conversion_event_unauthorized(
    api_client: APIClient,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:conversion-events-list")
    data = {"identity_identifier": identity.identifier}

    # When
    # No environment key header in use.
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_split_test_list_forbidden(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:split-tests-list")
    url = f"{url}?environment_id={environment.id}"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_split_test_list(
    staff_client: APIClient,
    with_environment_permissions: Callable[[list[str], int], None],
    environment: Environment,
    project: Project,
) -> None:
    # Given
    feature = Feature.objects.create(
        name="single feature for test",
        project=project,
        initial_value="200",
        is_server_key_only=True,
        default_enabled=True,
    )

    # Create a second environment to ensure the results are just
    # set for the former one.
    environment2 = Environment.objects.create(
        project=project, name="unrelated environment"
    )

    multivariate_feature_option1 = MultivariateFeatureOption.objects.create(
        feature=feature,
        default_percentage_allocation=30,
        type=STRING,
        string_value="mv_feature_option1",
    )
    multivariate_feature_option2 = MultivariateFeatureOption.objects.create(
        feature=feature,
        default_percentage_allocation=70,
        type=STRING,
        string_value="mv_feature_option2",
    )

    SplitTest.objects.create(
        environment=environment,
        feature=feature,
        multivariate_feature_option=multivariate_feature_option1,
        evaluation_count=100,
        conversion_count=10,
        pvalue=0.2,
        statistic=15,
    )

    SplitTest.objects.create(
        environment=environment,
        feature=feature,
        multivariate_feature_option=multivariate_feature_option2,
        evaluation_count=111,
        conversion_count=20,
        pvalue=0.2,
        statistic=15,
    )

    # Create unrelated environment split test for filtering.
    SplitTest.objects.create(
        environment=environment2,
        feature=feature,
        multivariate_feature_option=multivariate_feature_option1,
        evaluation_count=100,
        conversion_count=10,
        pvalue=0.2,
        statistic=15,
    )

    with_environment_permissions([VIEW_ENVIRONMENT])
    url = reverse("api-v1:split-tests-list")
    url = f"{url}?environment_id={environment.id}"

    # When
    response = staff_client.get(url)

    # Then
    assert response.data["count"] == 2

    result1 = response.data["results"][0]
    assert result1["conversion_count"] == 10
    assert result1["evaluation_count"] == 100
    assert result1["feature"]["id"] == feature.id
    assert result1["feature"]["name"] == feature.name
    assert (
        result1["multivariate_feature_option"]["id"] == multivariate_feature_option1.id
    )
    assert result1["multivariate_feature_option"]["type"] == "unicode"
    assert (
        result1["multivariate_feature_option"]["string_value"] == "mv_feature_option1"
    )

    result2 = response.data["results"][1]
    assert result2["conversion_count"] == 20
    assert result2["evaluation_count"] == 111
    assert result2["feature"]["id"] == feature.id
    assert result2["feature"]["name"] == feature.name
    assert (
        result2["multivariate_feature_option"]["id"] == multivariate_feature_option2.id
    )
    assert result2["multivariate_feature_option"]["type"] == "unicode"
    assert (
        result2["multivariate_feature_option"]["string_value"] == "mv_feature_option2"
    )
