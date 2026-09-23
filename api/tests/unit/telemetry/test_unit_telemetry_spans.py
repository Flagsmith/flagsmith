import pytest

from telemetry.spans import get_span_attribute, set_span_attribute


@pytest.mark.usefixtures("recording_span")
def test_set_span_attribute__recording_span__attribute_round_trips() -> None:
    # Given
    attribute = "organisation.id"

    # When
    set_span_attribute(attribute, 42)

    # Then
    assert get_span_attribute(attribute) == 42


def test_set_span_attribute__no_recording_span__silently_ignored() -> None:
    # Given
    attribute = "organisation.id"

    # When
    set_span_attribute(attribute, 42)

    # Then
    assert get_span_attribute(attribute) is None


def test_get_span_attribute__no_recording_span__returns_none() -> None:
    # Given
    attribute = "organisation.id"

    # When
    value = get_span_attribute(attribute)

    # Then
    assert value is None
