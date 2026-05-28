from features.feature_external_resources.models import ResourceType
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_API_VERSION,
    AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
    AZURE_DEVOPS_TAG_COLOR,
    AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE,
    AzureDevOpsTagLabel,
)


def test_constants__timeout__has_sensible_default() -> None:
    # Given
    timeout = AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS

    # When
    is_positive_int = isinstance(timeout, int) and timeout > 0

    # Then
    assert is_positive_int
    assert timeout <= 60


def test_constants__api_version__is_string() -> None:
    # Given
    version = AZURE_DEVOPS_API_VERSION

    # When
    is_string = isinstance(version, str)

    # Then
    assert is_string
    assert version


def test_tag_color__shape__is_hex_string() -> None:
    # Given
    colour = AZURE_DEVOPS_TAG_COLOR

    # When
    is_hex = isinstance(colour, str) and colour.startswith("#") and len(colour) == 7

    # Then
    assert is_hex


def test_tag_label_enum__members__are_short_human_labels() -> None:
    # Given
    expected = {
        "PR Open",
        "PR Merged",
        "PR Abandoned",
        "PR Draft",
        "Work Item Open",
        "Work Item Closed",
    }

    # When
    actual = {member.value for member in AzureDevOpsTagLabel}

    # Then
    assert actual == expected


def test_kind_by_label__all_members__map_to_pr_or_work_item() -> None:
    # Given
    valid_kinds = {"PR", "Work Item"}

    # When
    kinds = set(AZURE_DEVOPS_TAG_KIND_BY_LABEL.values())

    # Then
    assert kinds <= valid_kinds
    assert set(AZURE_DEVOPS_TAG_KIND_BY_LABEL.keys()) == set(AzureDevOpsTagLabel)


def test_kind_by_resource_type__keys__cover_both_azure_devops_resource_types() -> None:
    # Given
    expected_keys = {
        ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        ResourceType.AZURE_DEVOPS_WORK_ITEM.value,
    }

    # When
    actual_keys = set(AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE.keys())

    # Then
    assert actual_keys == expected_keys


def test_description_by_label__keys__cover_every_member() -> None:
    # Given
    expected_keys = set(AzureDevOpsTagLabel)

    # When
    actual_keys = set(AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL.keys())

    # Then
    assert actual_keys == expected_keys
