import pytest

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    WRITE_ONLY_PLACEHOLDER,
    AzureDevOpsConfigurationSerializer,
)
from integrations.azure_devops.serializers.browse import (
    AdoBrowseQueryParamsSerializer,
    AdoPullRequestsQueryParamsSerializer,
    AdoRepositoriesQueryParamsSerializer,
    AdoWorkItemsQueryParamsSerializer,
)


@pytest.mark.django_db
def test_serializer__to_representation__masks_personal_access_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    serializer = AzureDevOpsConfigurationSerializer(instance=azure_devops_configuration)

    # When
    data = serializer.data

    # Then
    assert data["personal_access_token"] == WRITE_ONLY_PLACEHOLDER
    assert data["organisation_url"] == azure_devops_configuration.organisation_url
    assert data["labeling_enabled"] is False
    assert data["tagging_enabled"] is False


@pytest.mark.django_db
def test_serializer__update_with_placeholder_pat__preserves_existing_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    original_token = azure_devops_configuration.personal_access_token
    serializer = AzureDevOpsConfigurationSerializer(
        instance=azure_devops_configuration,
        data={
            "organisation_url": azure_devops_configuration.organisation_url,
            "personal_access_token": WRITE_ONLY_PLACEHOLDER,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Then
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == original_token


@pytest.mark.django_db
def test_serializer__update_with_new_pat__persists_new_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    new_token = "ado-rotated-token"
    serializer = AzureDevOpsConfigurationSerializer(
        instance=azure_devops_configuration,
        data={
            "organisation_url": azure_devops_configuration.organisation_url,
            "personal_access_token": new_token,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Then
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == new_token


def test_browse_serializer__defaults__top_100_no_token() -> None:
    # Given
    serializer = AdoBrowseQueryParamsSerializer(data={})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data == {"top": 100}


def test_browse_serializer__valid_top_and_token__validates() -> None:
    # Given
    serializer = AdoBrowseQueryParamsSerializer(
        data={"top": 50, "continuation_token": "abc"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data == {"top": 50, "continuation_token": "abc"}


def test_browse_serializer__top_too_large__invalidates() -> None:
    # Given
    serializer = AdoBrowseQueryParamsSerializer(data={"top": 1000})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "top" in serializer.errors


def test_repositories_serializer__missing_ado_project_id__invalidates() -> None:
    # Given
    serializer = AdoRepositoriesQueryParamsSerializer(data={})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "ado_project_id" in serializer.errors


def test_pull_requests_serializer__state_default__is_active() -> None:
    # Given
    serializer = AdoPullRequestsQueryParamsSerializer(
        data={"ado_project_id": "00000000-0000-0000-0000-0000000000aa"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data["state"] == "active"


def test_pull_requests_serializer__invalid_state__rejected() -> None:
    # Given
    serializer = AdoPullRequestsQueryParamsSerializer(
        data={
            "ado_project_id": "00000000-0000-0000-0000-0000000000aa",
            "state": "weird",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "state" in serializer.errors


def test_work_items_serializer__all_fields_optional_except_project__validates() -> None:
    # Given
    serializer = AdoWorkItemsQueryParamsSerializer(
        data={"ado_project_id": "00000000-0000-0000-0000-0000000000aa"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data["ado_project_id"] == (
        "00000000-0000-0000-0000-0000000000aa"
    )


def test_work_items_serializer__with_filters__validates() -> None:
    # Given
    serializer = AdoWorkItemsQueryParamsSerializer(
        data={
            "ado_project_id": "00000000-0000-0000-0000-0000000000aa",
            "search_text": "login",
            "state": "Active",
            "work_item_type": "Bug",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data["search_text"] == "login"
    assert serializer.validated_data["state"] == "Active"
    assert serializer.validated_data["work_item_type"] == "Bug"


def test_work_items_serializer__negative_continuation_token__rejected() -> None:
    # Given
    serializer = AdoWorkItemsQueryParamsSerializer(
        data={
            "ado_project_id": "00000000-0000-0000-0000-0000000000aa",
            "continuation_token": -1,
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "continuation_token" in serializer.errors


def test_work_items_serializer__non_integer_continuation_token__rejected() -> None:
    # Given
    serializer = AdoWorkItemsQueryParamsSerializer(
        data={
            "ado_project_id": "00000000-0000-0000-0000-0000000000aa",
            "continuation_token": "abc",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "continuation_token" in serializer.errors
