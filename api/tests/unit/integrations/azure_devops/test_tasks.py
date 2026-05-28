import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature, FeatureState
from integrations.azure_devops.tasks import (
    apply_azure_devops_label,
    post_azure_devops_feature_deleted_comment,
    post_azure_devops_linked_comment,
    post_azure_devops_state_change_comment,
    post_azure_devops_unlinked_comment,
    remove_azure_devops_label,
)


@pytest.mark.django_db
def test_post_linked_task__valid_id__forwards_to_service(
    azure_devops_pr_resource_open: FeatureExternalResource,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch("integrations.azure_devops.tasks.post_linked_comment")

    # When
    post_azure_devops_linked_comment(azure_devops_pr_resource_open.id)

    # Then
    service_mock.assert_called_once_with(azure_devops_pr_resource_open)


@pytest.mark.django_db
def test_post_linked_task__missing_resource__noop(
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch("integrations.azure_devops.tasks.post_linked_comment")

    # When
    post_azure_devops_linked_comment(999999)

    # Then
    service_mock.assert_not_called()


@pytest.mark.django_db
def test_post_unlinked_task__valid_args__forwards_to_service(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch("integrations.azure_devops.tasks.post_unlinked_comment")

    # When
    post_azure_devops_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1",
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
        project_id=feature.project_id,
    )

    # Then
    service_mock.assert_called_once()


@pytest.mark.django_db
def test_post_state_change_task__valid_id__forwards_to_service(
    feature: Feature,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    feature_state = (
        FeatureState.objects.get_live_feature_states(environment=environment)
        .filter(feature=feature, identity__isnull=True, feature_segment__isnull=True)
        .first()
    )
    assert feature_state is not None
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.post_state_change_comment"
    )

    # When
    post_azure_devops_state_change_comment(feature_state.id)

    # Then
    service_mock.assert_called_once()


@pytest.mark.django_db
def test_post_state_change_task__missing_feature_state__noop(
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.post_state_change_comment"
    )

    # When
    post_azure_devops_state_change_comment(999999)

    # Then
    service_mock.assert_not_called()


@pytest.mark.django_db
def test_post_feature_deleted_task__valid_args__forwards_to_service(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.post_feature_deleted_comment"
    )

    # When
    post_azure_devops_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    service_mock.assert_called_once()


@pytest.mark.django_db
def test_apply_label_task__valid_id__forwards_to_service(
    azure_devops_pr_resource_open: FeatureExternalResource,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.apply_flagsmith_label_to_resource"
    )

    # When
    apply_azure_devops_label(azure_devops_pr_resource_open.id)

    # Then
    service_mock.assert_called_once_with(azure_devops_pr_resource_open)


@pytest.mark.django_db
def test_apply_label_task__missing_resource__noop(
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.apply_flagsmith_label_to_resource"
    )

    # When
    apply_azure_devops_label(999999)

    # Then
    service_mock.assert_not_called()


@pytest.mark.django_db
def test_remove_label_task__valid_args__forwards_to_service(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.remove_flagsmith_label_from_resource"
    )

    # When
    remove_azure_devops_label(
        project_id=feature.project_id,
        resource_url=("https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1"),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    service_mock.assert_called_once_with(
        project_id=feature.project_id,
        resource_url=("https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1"),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )
