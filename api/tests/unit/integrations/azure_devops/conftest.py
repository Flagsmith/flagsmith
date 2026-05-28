import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@pytest.fixture()
def azure_devops_configuration(project: Project) -> AzureDevOpsConfiguration:
    return AzureDevOpsConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        organisation_url="https://dev.azure.com/test-org",
        personal_access_token="ado-test-token",
    )


def _make_pr_resource(
    feature: Feature, *, pr_id: int, state: str, is_draft: bool = False
) -> FeatureExternalResource:
    metadata = (
        '{"state": "'
        + state
        + '", "is_draft": '
        + ("true" if is_draft else "false")
        + "}"
    )
    return FeatureExternalResource.objects.create(
        feature=feature,
        url=f"https://dev.azure.com/test-org/proj/_git/repo/pullrequest/{pr_id}",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata=metadata,
    )


def _make_work_item_resource(
    feature: Feature, *, state: str
) -> FeatureExternalResource:
    return FeatureExternalResource.objects.create(
        feature=feature,
        url=f"https://dev.azure.com/test-org/proj/_workitems/edit/{abs(hash(state)) % 10000}",
        type=ResourceType.AZURE_DEVOPS_WORK_ITEM.value,
        metadata='{"state": "' + state + '"}',
    )


@pytest.fixture()
def azure_devops_pr_resource_open(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, pr_id=1, state="active", is_draft=False)


@pytest.fixture()
def azure_devops_pr_resource_draft(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, pr_id=2, state="active", is_draft=True)


@pytest.fixture()
def azure_devops_pr_resource_merged(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, pr_id=3, state="completed")


@pytest.fixture()
def azure_devops_work_item_resource_open(feature: Feature) -> FeatureExternalResource:
    return _make_work_item_resource(feature, state="Active")


@pytest.fixture()
def azure_devops_work_item_resource_closed(
    feature: Feature,
) -> FeatureExternalResource:
    return _make_work_item_resource(feature, state="Closed")
