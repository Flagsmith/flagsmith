from features.feature_external_resources.models import (
    AZURE_DEVOPS_RESOURCE_TYPES,
    GITLAB_RESOURCE_TYPES,
    ResourceType,
)


def test_resource_type__azure_devops_pull_request__has_value_and_label() -> None:
    # Given / When / Then
    assert ResourceType.AZURE_DEVOPS_PULL_REQUEST.value == "AZURE_DEVOPS_PULL_REQUEST"
    assert ResourceType.AZURE_DEVOPS_PULL_REQUEST.label == "Azure DevOps Pull Request"


def test_resource_type__azure_devops_work_item__has_value_and_label() -> None:
    # Given / When / Then
    assert ResourceType.AZURE_DEVOPS_WORK_ITEM.value == "AZURE_DEVOPS_WORK_ITEM"
    assert ResourceType.AZURE_DEVOPS_WORK_ITEM.label == "Azure DevOps Work Item"


def test_azure_devops_resource_types__contains_pull_request_and_work_item__matches_expected_set() -> None:
    # Given / When
    members = set(AZURE_DEVOPS_RESOURCE_TYPES)

    # Then
    assert members == {
        ResourceType.AZURE_DEVOPS_PULL_REQUEST,
        ResourceType.AZURE_DEVOPS_WORK_ITEM,
    }


def test_resource_type_groupings__azure_devops_and_gitlab__are_disjoint() -> None:
    # Given / When / Then
    assert set(AZURE_DEVOPS_RESOURCE_TYPES).isdisjoint(set(GITLAB_RESOURCE_TYPES))
