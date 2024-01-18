import json
from typing import Callable

from app_analytics.split_testing.models import (
    ConversionEvent,
    ConversionEventType,
    SplitTest,
)
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


def test_create_conversion_event(
    api_client: APIClient,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:conversion-events")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    _type = "paid_plan"
    data = {"identity_identifier": identity.identifier, "type": _type}

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data is None

    assert ConversionEvent.objects.count() == 1
    assert ConversionEventType.objects.count() == 1

    conversion_event = ConversionEvent.objects.first()
    assert conversion_event.identity == identity
    assert conversion_event.environment == environment

    assert conversion_event.type.name == _type
    assert conversion_event.type.environment == environment


def test_create_conversion_event_unauthorized(
    api_client: APIClient,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:conversion-events")
    data = {"identity_identifier": identity.identifier}

    # When
    # No environment key header in use.
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_conversion_event_type_list_forbidden(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    url = reverse("api-v1:conversion-event-types")
    url += f"?environment_id={environment.id}"

    # When
    # Staff is missing VIEW_ENVIRONMENT permission
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_conversion_event_type_list(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: Callable[[list[str], int], None],
    project: Project,
) -> None:
    # Create two target CETs.
    ConversionEventType.objects.create(
        environment=environment,
        name="free_plan",
    )
    ConversionEventType.objects.create(
        environment=environment,
        name="paid_plan",
    )

    unrelated_environment = Environment.objects.create(
        project=project, name="unrelated environment"
    )

    # Create an unrelated CET.
    ConversionEventType.objects.create(
        environment=unrelated_environment,
        name="free_plan",
    )

    with_environment_permissions([VIEW_ENVIRONMENT])
    url = reverse("api-v1:conversion-event-types")
    url += f"?environment_id={environment.id}"

    # When
    response = staff_client.get(url)

    # Then
    assert response.data["count"] == 2
    assert response.data["results"][0]["name"] == "free_plan"
    assert response.data["results"][1]["name"] == "paid_plan"


def test_split_test_list_forbidden(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    cet = ConversionEventType.objects.create(
        environment=environment,
        name="free_plan",
    )

    url = reverse("api-v1:split-tests-list")
    url = f"{url}?conversion_event_type_id={cet.id}"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_split_test_list(
    staff_client: APIClient,
    with_environment_permissions: Callable[[list[str], int], None],
    environment: Environment,
    project: Project,
    django_assert_num_queries: Callable[[int], None],
) -> None:
    # Given
    feature = Feature.objects.create(
        name="single_feature_for_test",
        project=project,
        initial_value="feature",
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
        default_percentage_allocation=30,
        type=STRING,
        string_value="mv_feature_option2",
    )

    cet1 = ConversionEventType.objects.create(
        environment=environment,
        name="free_plan",
    )

    SplitTest.objects.create(
        conversion_event_type=cet1,
        environment=environment,
        feature=feature,
        multivariate_feature_option=None,
        evaluation_count=123,
        conversion_count=12,
        pvalue=0.2,
    )

    SplitTest.objects.create(
        conversion_event_type=cet1,
        environment=environment,
        feature=feature,
        multivariate_feature_option=multivariate_feature_option1,
        evaluation_count=100,
        conversion_count=10,
        pvalue=0.2,
    )

    SplitTest.objects.create(
        conversion_event_type=cet1,
        environment=environment,
        feature=feature,
        multivariate_feature_option=multivariate_feature_option2,
        evaluation_count=111,
        conversion_count=20,
        pvalue=0.2,
    )

    # Create unrelated environment split test for filtering.
    cet2 = ConversionEventType.objects.create(
        environment=environment2,
        name="free_plan",
    )
    SplitTest.objects.create(
        conversion_event_type=cet2,
        environment=environment2,
        feature=feature,
        multivariate_feature_option=multivariate_feature_option1,
        evaluation_count=100,
        conversion_count=10,
        pvalue=0.2,
    )

    with_environment_permissions([VIEW_ENVIRONMENT])
    url = reverse("api-v1:split-tests-list")
    url = f"{url}?conversion_event_type_id={cet1.id}"
    expected_query_count = 9

    # When
    with django_assert_num_queries(expected_query_count):
        response = staff_client.get(url)

    # Then
    assert response.data["count"] == 3

    result1 = response.data["results"][0]
    assert result1["conversion_count"] == 12
    assert result1["evaluation_count"] == 123
    assert result1["feature"]["id"] == feature.id
    assert result1["feature"]["name"] == feature.name
    assert result1["value_data"] == {
        "boolean_value": None,
        "integer_value": None,
        "string_value": "feature",
        "type": "unicode",
    }

    result2 = response.data["results"][1]
    assert result2["conversion_count"] == 10
    assert result2["evaluation_count"] == 100
    assert result2["feature"]["id"] == feature.id
    assert result2["feature"]["name"] == feature.name
    assert result2["value_data"] == {
        "boolean_value": None,
        "integer_value": None,
        "string_value": "mv_feature_option1",
        "type": "unicode",
    }

    result3 = response.data["results"][2]
    assert result3["conversion_count"] == 20
    assert result3["evaluation_count"] == 111
    assert result3["feature"]["id"] == feature.id
    assert result3["feature"]["name"] == feature.name
    assert result3["value_data"] == {
        "boolean_value": None,
        "integer_value": None,
        "string_value": "mv_feature_option2",
        "type": "unicode",
    }
