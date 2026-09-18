import pytest
from django.core.exceptions import ValidationError
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture

from core.fields import EncryptedJSONField, NoSSRFURLField
from integrations.gitlab.serializers import GitLabConfigurationSerializer


@pytest.mark.parametrize(
    "url,expected_code",
    [
        ("http://127.0.0.1/", "internal_address"),
        ("ftp://example.com/", "invalid"),
    ],
)
def test_no_ssrf_url_field__unsafe_url__raises_validation_error(  # noqa: FT004
    url: str,
    expected_code: str,
) -> None:
    # Given
    field: NoSSRFURLField[str, str] = NoSSRFURLField()

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        field.run_validators(url)

    assert exc_info.value.error_list[0].code == expected_code


def test_no_ssrf_url_field__model_serializer__validates_internal_address() -> None:
    # Given — `GitLabConfiguration.gitlab_instance_url` is a `NoSSRFURLField`,
    # so DRF copies its validators onto the field it builds for the serialiser
    # without the serialiser having to declare one.
    serializer = GitLabConfigurationSerializer(
        data={
            "gitlab_instance_url": "http://127.0.0.1/",
            "access_token": "glpat-xxxxxxxxxxxxxxxxxxxx",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "internal_address" in str(serializer.errors["gitlab_instance_url"])


def test_no_ssrf_url_field__model_serializer__rejects_non_http_scheme() -> None:
    # Given — DRF discards the `URLValidator` it copies from the model field and
    # substitutes its own, which permits ftp(s). The scheme check therefore lives
    # in a plain function validator, which DRF leaves alone. Restoring it to a
    # `URLValidator` on the field would let this through.
    serializer = GitLabConfigurationSerializer(
        data={
            "gitlab_instance_url": "ftp://example.com/",
            "access_token": "glpat-xxxxxxxxxxxxxxxxxxxx",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False


def test_get_prep_value__json_value__returns_ciphertext_that_roundtrips() -> None:
    # Given
    field = EncryptedJSONField()
    value = {"password": "hunter2"}

    # When
    stored = field.get_prep_value(value)

    # Then
    assert stored is not None
    assert "hunter2" not in stored
    assert field.from_db_value(stored, None, None) == value


def test_field_methods__none__returns_none() -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    assert field.get_prep_value(None) is None
    assert field.from_db_value(None, None, None) is None


def test_from_db_value__secret_key_changed__returns_none_and_logs(
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.WAREHOUSE_CREDENTIALS_SECRET = "old-secret"
    field = EncryptedJSONField()
    stored = field.get_prep_value({"password": "hunter2"})
    settings.WAREHOUSE_CREDENTIALS_SECRET = "new-secret"

    # When
    value = field.from_db_value(stored, None, None)

    # Then
    assert value is None
    assert {
        "level": "warning",
        "event": "encrypted_field.decrypt_failed",
    } in [{"level": e["level"], "event": e["event"]} for e in log.events]


def test_get_lookup__non_isnull__raises_not_implemented() -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    with pytest.raises(NotImplementedError):
        field.get_lookup("exact")
    assert field.get_lookup("isnull") is not None
