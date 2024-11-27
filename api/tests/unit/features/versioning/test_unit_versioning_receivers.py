import logging
import uuid

import pytest
from pytest_mock import MockerFixture

from features.versioning.receivers import add_existing_feature_states


def test_add_existing_feature_states_logs_error_if_invalid_feature_state_found(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """
    This test is here to validate that we log the correct message in the case that
    a feature state on the previous version is not valid for the environment /
    feature combination. Since this is not a valid use case, and we are just trying
    to track down how, and where this can happen, we are mocking certain elements of
    the test to simplify it.
    """

    # Given
    valid_feature_id = 1
    invalid_feature_id = 2

    valid_feature_state = mocker.MagicMock(feature_id=valid_feature_id)
    invalid_feature_state = mocker.MagicMock(feature_id=invalid_feature_id)

    previous_environment_feature_version = mocker.MagicMock()
    previous_environment_feature_version.feature_states.all.return_value = [
        valid_feature_state,
        invalid_feature_state,
    ]

    instance = mocker.MagicMock(feature_id=valid_feature_id, uuid=str(uuid.uuid4()))
    instance.get_previous_version.return_value = previous_environment_feature_version

    # When
    add_existing_feature_states(instance, created=True)

    # Then
    assert caplog.record_tuples == [
        (
            "features.versioning.receivers",
            logging.ERROR,
            f"Not cloning feature state for feature {invalid_feature_id} into version {instance.uuid}, "
            f"which belongs to feature {valid_feature_id}",
        )
    ]
