import pytest
import responses

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.comments import post_linked_comment

ORG_URL = "https://dev.azure.com/test-org"


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__pr_resource__posts_thread(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    environment: object,  # noqa: ARG001 - existence triggers env state in template
) -> None:
    # Given
    expected_url = f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads"
    responses.post(expected_url, json={"id": 1})

    # When
    post_linked_comment(azure_devops_pr_resource_open)

    # Then
    [call] = responses.calls
    body = call.request.body
    assert body is not None
    body_text = body.decode() if isinstance(body, bytes) else body
    assert "Linked to Flagsmith feature flag" in body_text


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__work_item_resource__posts_comment(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_work_item_resource_open: FeatureExternalResource,
    environment: object,  # noqa: ARG001
) -> None:
    # Given — work-item URL from the conftest fixture is
    # "https://dev.azure.com/test-org/proj/_workitems/edit/<hash%10000>"
    # so the work_item_id varies; the regex captures the integer.
    import re

    match = re.search(
        r"_workitems/edit/(\d+)",
        azure_devops_work_item_resource_open.url,
    )
    assert match is not None
    work_item_id = int(match.group(1))

    expected_url = (
        f"{ORG_URL}/proj/_apis/wit/workItems/{work_item_id}/comments"
    )
    responses.post(expected_url, json={"id": 1})

    # When
    post_linked_comment(azure_devops_work_item_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__no_configuration__noop(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — no AzureDevOpsConfiguration exists

    # When
    post_linked_comment(azure_devops_pr_resource_open)

    # Then — no outbound call was made
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__ado_500__logs_and_returns(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    expected_url = f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads"
    responses.post(expected_url, json={}, status=500)

    # When — must not raise
    post_linked_comment(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__unparseable_url__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    from features.feature_external_resources.models import (
        FeatureExternalResource,
        ResourceType,
    )

    bogus = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://example.com/not/an/ado/url",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata='{"state": "active", "is_draft": false}',
    )

    # When
    post_linked_comment(bogus)

    # Then — URL parsing returns None; no call attempted
    assert len(responses.calls) == 0
