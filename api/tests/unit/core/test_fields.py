import pytest
from django.core.exceptions import ValidationError

from core.fields import NoSSRFURLField
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
