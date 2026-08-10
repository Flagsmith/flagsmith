from unittest.mock import MagicMock, Mock

import pytest
from django.utils import timezone
from pytest_mock import MockerFixture

from environments.models import Environment
from environments.onboarding.services import record_environment_first_evaluation


@pytest.fixture(autouse=True)
def write_environment_documents(mocker: MockerFixture) -> Mock:
    return mocker.patch.object(Environment, "write_environment_documents")


@pytest.fixture()
def mock_openfeature_client(mocker: MockerFixture) -> MagicMock:
    mock_client: MagicMock = mocker.MagicMock()
    mocker.patch(
        "environments.onboarding.services.get_openfeature_client",
        return_value=mock_client,
    )
    return mock_client


def test_record_environment_first_evaluation__first_evaluation__tracks_conversion_event(
    environment: Environment,
    mock_openfeature_client: MagicMock,
) -> None:
    # Given
    organisation_id = environment.project.organisation_id

    # When
    record_environment_first_evaluation(environment, "flagsmith-python-sdk")

    # Then
    mock_openfeature_client.track.assert_called_once()
    call_args = mock_openfeature_client.track.call_args
    assert call_args.args == ("environment.first_evaluated",)
    assert (
        call_args.kwargs["evaluation_context"].targeting_key == f"org.{organisation_id}"
    )
    assert call_args.kwargs["tracking_event_details"].attributes == {
        "sdk_label": "flagsmith-python-sdk",
    }


def test_record_environment_first_evaluation__org_targeting_key_set__tracks_with_stored_key(
    environment: Environment,
    mock_openfeature_client: MagicMock,
) -> None:
    # Given
    organisation = environment.project.organisation
    organisation.targeting_key = "a" * 32
    organisation.save(update_fields=["targeting_key"])

    # When
    record_environment_first_evaluation(environment, "flagsmith-python-sdk")

    # Then
    call_args = mock_openfeature_client.track.call_args
    assert call_args.kwargs["evaluation_context"].targeting_key == "a" * 32


def test_record_environment_first_evaluation__already_evaluated__does_not_track(
    environment: Environment,
    mock_openfeature_client: MagicMock,
) -> None:
    # Given
    environment.first_evaluated_at = timezone.now()
    environment.save(update_fields=["first_evaluated_at"])

    # When
    record_environment_first_evaluation(environment, "flagsmith-python-sdk")

    # Then
    mock_openfeature_client.track.assert_not_called()
