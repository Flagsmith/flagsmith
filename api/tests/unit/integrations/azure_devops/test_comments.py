import pytest
import responses
from pytest_mock import MockerFixture
from task_processor.decorators import TaskHandler

from environments.models import Environment
from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.comments import (
    post_feature_deleted_comment,
    post_linked_comment,
    post_state_change_comment,
    post_state_change_comment_for_feature_state,
    post_unlinked_comment,
)

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

    expected_url = f"{ORG_URL}/proj/_apis/wit/workItems/{work_item_id}/comments"
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


@pytest.mark.django_db
@responses.activate
def test_post_unlinked_comment__pr_resource__posts_thread(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    expected_url = f"{ORG_URL}/proj/_apis/git/pullrequests/77/threads"
    responses.post(expected_url, json={"id": 1})

    # When
    post_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url=("https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
        project_id=feature.project_id,
    )

    # Then
    [call] = responses.calls
    body = call.request.body
    assert body is not None
    body_text = body.decode() if isinstance(body, bytes) else body
    assert "Unlinked from Flagsmith" in body_text


@pytest.mark.django_db
@responses.activate
def test_post_unlinked_comment__no_configuration__noop(
    feature: Feature,
) -> None:
    # Given — no AzureDevOpsConfiguration exists

    # When
    post_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url=("https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__multiple_linked_resources__posts_to_each(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_work_item_resource_open: FeatureExternalResource,
    feature: Feature,
) -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads",
        json={"id": 1},
    )
    import re

    match = re.search(
        r"_workitems/edit/(\d+)",
        azure_devops_work_item_resource_open.url,
    )
    assert match is not None
    work_item_id = int(match.group(1))
    responses.post(
        f"{ORG_URL}/proj/_apis/wit/workItems/{work_item_id}/comments",
        json={"id": 1},
    )

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 2


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__no_linked_resources__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given — no FeatureExternalResource rows of AZURE_DEVOPS_* type

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__no_configuration__noop(
    feature: Feature,
) -> None:
    # Given — no AzureDevOpsConfiguration exists

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__environment_scope__posts_to_each_resource(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = (
        FeatureState.objects.get_live_feature_states(environment=environment)
        .filter(feature=feature, identity__isnull=True, feature_segment__isnull=True)
        .first()
    )
    assert feature_state is not None
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads",
        json={"id": 1},
    )

    # When
    post_state_change_comment(feature_state)

    # Then
    [call] = responses.calls
    body = call.request.body
    assert body is not None
    body_text = body.decode() if isinstance(body, bytes) else body
    assert feature.name in body_text


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__no_resources_linked__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given — no FeatureExternalResource rows
    from features.models import FeatureState

    feature_state = (
        FeatureState.objects.get_live_feature_states(environment=environment)
        .filter(feature=feature, identity__isnull=True, feature_segment__isnull=True)
        .first()
    )
    assert feature_state is not None

    # When
    post_state_change_comment(feature_state)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__no_configuration__noop(
    azure_devops_pr_resource_open: FeatureExternalResource,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given — no AzureDevOpsConfiguration
    from features.models import FeatureState

    feature_state = (
        FeatureState.objects.get_live_feature_states(environment=environment)
        .filter(feature=feature, identity__isnull=True, feature_segment__isnull=True)
        .first()
    )
    assert feature_state is not None

    # When
    post_state_change_comment(feature_state)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
def test_post_state_change_comment_for_feature_state__with_config__queues_task(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = (
        FeatureState.objects.get_live_feature_states(environment=environment)
        .filter(feature=feature, identity__isnull=True, feature_segment__isnull=True)
        .first()
    )
    assert feature_state is not None
    delay_mock = mocker.patch.object(TaskHandler, "delay")

    # When
    post_state_change_comment_for_feature_state(feature_state)

    # Then
    delay_mock.assert_called_once_with(args=(feature_state.id,))


@pytest.mark.django_db
def test_post_state_change_comment_for_feature_state__no_config__skips_dispatch(
    feature: Feature,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given — no AzureDevOpsConfiguration
    from features.models import FeatureState

    feature_state = (
        FeatureState.objects.get_live_feature_states(environment=environment)
        .filter(feature=feature, identity__isnull=True, feature_segment__isnull=True)
        .first()
    )
    assert feature_state is not None
    delay_mock = mocker.patch.object(TaskHandler, "delay")

    # When
    post_state_change_comment_for_feature_state(feature_state)

    # Then
    delay_mock.assert_not_called()
