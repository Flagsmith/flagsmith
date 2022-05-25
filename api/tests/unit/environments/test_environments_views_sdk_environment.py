from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment, EnvironmentAPIKey
from features.models import Feature
from segments.models import EQUAL, Condition, Segment, SegmentRule


def test_get_environment_document(
    organisation_one, organisation_one_project_one, django_assert_num_queries
):
    # Given
    project = organisation_one_project_one

    # an environment
    environment = Environment.objects.create(name="Test Environment", project=project)
    api_key = EnvironmentAPIKey.objects.create(environment=environment)
    client = APIClient()
    client.credentials(HTTP_X_ENVIRONMENT_KEY=api_key.key)

    # and some other sample data to make sure we're testing all of the document
    Feature.objects.create(name="test_feature", project=project)
    for i in range(10):
        segment = Segment.objects.create(project=project)
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            operator=EQUAL,
            property=f"property_{i}",
            value=f"value_{i}",
            rule=segment_rule,
        )
        nested_rule = SegmentRule.objects.create(
            segment=segment, rule=segment_rule, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            operator=EQUAL,
            property=f"nested_prop_{i}",
            value=f"nested_value_{i}",
            rule=nested_rule,
        )

    # and the relevant URL to get an environment document
    url = reverse("api-v1:environment-document")

    # When
    with django_assert_num_queries(12):
        response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()


def test_get_environment_document_fails_with_invalid_key(
    organisation_one, organisation_one_project_one
):
    # Given
    project = organisation_one_project_one

    # an environment
    environment = Environment.objects.create(name="Test Environment", project=project)
    client = APIClient()

    # and we use the regular 'client' API key from the environment
    client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # and the relevant URL to get an environment document
    url = reverse("api-v1:environment-document")

    # When
    response = client.get(url)

    # Then
    # We get a 403 since only the server side API keys are able to access the
    # environment document
    assert response.status_code == status.HTTP_403_FORBIDDEN
