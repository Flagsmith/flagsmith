import json
import os.path
from unittest.mock import mock_open, patch

import pytest
import responses
from django.conf import settings

from integrations.flagsmith.client import FlagsmithWrapper


@pytest.mark.parametrize(
    "feature_value, feature_enabled",
    (
        (42, True),
        (42, False),
        (True, False),
        (False, False),
        (True, True),
        (False, True),
        ("foo", True),
        ("foo", False),
    ),
)
@responses.activate()
def test_flagsmith_wrapper_builds_defaults_from_json_file(
    feature_value, feature_enabled
):
    # Given
    environment_key = "not-a-real-key"
    api_url = "https://broken.flagsmith.com/api/v1"
    responses.add(method="GET", url=api_url, status=404)

    feature_name = "my_feature"

    defaults_data = json.dumps(
        [
            {
                "feature_state_value": feature_value,
                "enabled": feature_enabled,
                "feature": {"id": 1, "type": "STANDARD", "name": feature_name},
            }
        ]
    )

    # When
    with patch("builtins.open", mock_open(read_data=defaults_data)) as mock_file:
        wrapper = FlagsmithWrapper(environment_key=environment_key, api_url=api_url)

        # Then
        mock_file.assert_called_with(
            os.path.join(settings.BASE_DIR, "integrations/flagsmith/defaults.json")
        )
        assert wrapper._client

        # let's verify that it's using the defaults as we expect
        flags = wrapper.get_client().get_environment_flags()
        assert flags.is_feature_enabled(feature_name) == feature_enabled
        assert flags.get_feature_value(feature_name) == feature_value


def test_flagsmith_wrapper_get_instance(mocker, settings):
    # Given
    mocker.patch("integrations.flagsmith.client._flagsmith_wrapper", None)

    settings.FLAGSMITH_SERVER_KEY = "some-key"
    settings.FLAGSMITH_API_URL = "https://edge.api.flagsmith.com/api/v1"

    # When
    wrapper: FlagsmithWrapper = FlagsmithWrapper.get_instance()

    # Then
    # we have a wrapper instance
    assert wrapper

    # and further requests to get_instance just return the same instance
    assert FlagsmithWrapper.get_instance() == wrapper
