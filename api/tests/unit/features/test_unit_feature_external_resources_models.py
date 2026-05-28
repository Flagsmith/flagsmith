from features.feature_external_resources.models import (
    AZURE_DEVOPS_RESOURCE_TYPES,
    GITLAB_RESOURCE_TYPES,
    ResourceType,
)


def test_resource_type__azure_devops_pull_request__has_value_and_label() -> None:
    # Given
    member = ResourceType.AZURE_DEVOPS_PULL_REQUEST

    # When
    value = member.value
    label = member.label

    # Then
    assert value == "AZURE_DEVOPS_PULL_REQUEST"
    assert label == "Azure DevOps Pull Request"


def test_resource_type__azure_devops_work_item__has_value_and_label() -> None:
    # Given
    member = ResourceType.AZURE_DEVOPS_WORK_ITEM

    # When
    value = member.value
    label = member.label

    # Then
    assert value == "AZURE_DEVOPS_WORK_ITEM"
    assert label == "Azure DevOps Work Item"


def test_azure_devops_resource_types__contains_pull_request_and_work_item__matches_expected_set() -> (
    None
):
    # Given / When
    members = set(AZURE_DEVOPS_RESOURCE_TYPES)

    # Then
    assert members == {
        ResourceType.AZURE_DEVOPS_PULL_REQUEST,
        ResourceType.AZURE_DEVOPS_WORK_ITEM,
    }


def test_resource_type_groupings__azure_devops_and_gitlab__are_disjoint() -> None:
    # Given
    azure_devops_members = set(AZURE_DEVOPS_RESOURCE_TYPES)
    gitlab_members = set(GITLAB_RESOURCE_TYPES)

    # When
    overlap = azure_devops_members & gitlab_members

    # Then
    assert overlap == set()


def test_resource_type_field__choices__include_azure_devops_values() -> None:
    # Given
    from features.feature_external_resources.models import FeatureExternalResource

    # When
    field = FeatureExternalResource._meta.get_field("type")
    assert field.choices is not None
    choice_values = {value for value, _label in field.choices}

    # Then
    assert "AZURE_DEVOPS_PULL_REQUEST" in choice_values
    assert "AZURE_DEVOPS_WORK_ITEM" in choice_values
