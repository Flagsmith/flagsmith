from datetime import datetime, timezone

from django.forms import model_to_dict

from experimentation.mappers import map_sdk_event_to_sdk_experimentation_event


def test_map_sdk_event_to_sdk_experimentation_event__validated_event__maps_to_row() -> (
    None
):
    # Given
    collected_at = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
    event = {
        "event": "purchase",
        "feature_name": "checkout",
        "timestamp": 1_793_534_400_007,
        "value": {"amount": 42},
        "traits": {"plan": "pró"},
        "metadata": "sdk-note",
    }

    # When
    row = map_sdk_event_to_sdk_experimentation_event(
        event,
        environment_key="env-key",
        collected_at=collected_at,
        sdk_language="python",
        sdk_version="6.2.3",
    )

    # Then
    assert model_to_dict(row, exclude=["id"]) == {
        "environment_key": "env-key",
        "event": "purchase",
        "feature_name": "checkout",
        "timestamp": datetime(2026, 11, 1, 12, 0, 0, 7000, tzinfo=timezone.utc),
        "collected_at": collected_at,
        "identifier": "",
        "value": '{"amount":42}',
        "traits": '{"plan":"pró"}',
        "metadata": "sdk-note",
        "sdk_language": "python",
        "sdk_version": "6.2.3",
    }
