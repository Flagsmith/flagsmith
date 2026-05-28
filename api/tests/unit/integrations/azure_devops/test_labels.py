import pytest
import responses

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.labels import (
    apply_flagsmith_label_to_resource,
    remove_flagsmith_label_from_resource,
)

ORG_URL = "https://dev.azure.com/test-org"


@pytest.mark.django_db
@responses.activate
def test_apply_label__pr_resource_and_labeling_enabled__posts_label(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/labels",
        json={"id": "x", "name": "flagsmith"},
    )

    # When
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_apply_label__labeling_disabled__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — labeling_enabled defaults to False
    assert azure_devops_configuration.labeling_enabled is False

    # When
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_apply_label__no_configuration__noop(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — no configuration exists

    # When
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_apply_label__work_item_resource__patches_tags(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    import re

    match = re.search(
        r"_workitems/edit/(\d+)",
        azure_devops_work_item_resource_open.url,
    )
    assert match is not None
    work_item_id = int(match.group(1))

    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/{work_item_id}",
        json={"id": work_item_id, "fields": {}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/{work_item_id}",
        json={"id": work_item_id, "fields": {"System.Tags": "flagsmith"}},
    )

    # When
    apply_flagsmith_label_to_resource(azure_devops_work_item_resource_open)

    # Then
    assert len(responses.calls) == 2


@pytest.mark.django_db
@responses.activate
def test_apply_label__ado_500__logs_and_returns(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/labels",
        json={},
        status=500,
    )

    # When — must not raise
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_remove_label__pr_resource_and_labeling_enabled__deletes(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.delete(
        f"{ORG_URL}/proj/_apis/git/pullrequests/77/labels/flagsmith",
        json={},
        status=204,
    )

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_remove_label__labeling_disabled__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given — labeling_enabled defaults to False

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_remove_label__no_configuration__noop(
    feature: Feature,
) -> None:
    # Given — no configuration

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_remove_label__work_item_resource__patches_filtered_tags(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/200",
        json={"id": 200, "fields": {"System.Tags": "alpha; flagsmith"}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/200",
        json={"id": 200, "fields": {"System.Tags": "alpha"}},
    )

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url="https://dev.azure.com/test-org/proj/_workitems/edit/200",
        resource_type="AZURE_DEVOPS_WORK_ITEM",
    )

    # Then
    assert len(responses.calls) == 2
