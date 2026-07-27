import pytest
from django.core.exceptions import ValidationError

from oauth2_metadata.services import validate_redirect_uri


@pytest.mark.parametrize(
    ("uri", "expected_message"),
    [
        ("not-a-uri", "Invalid URI"),
        ("claude:", "Invalid URI"),
        ("https://[::1", "Invalid URI"),
        ("https:///callback", "Invalid URI"),
        ("https://*.example.com/callback", "Wildcards"),
        ("https://example.com/callback#frag", "Fragment"),
        ("http://example.com/callback", "HTTPS is required"),
        ("javascript:alert(1)", "Scheme is not permitted"),
        ("JavaScript:alert(1)", "Scheme is not permitted"),
        ("data:text/html,x", "Scheme is not permitted"),
        ("file:///etc/passwd", "Scheme is not permitted"),
    ],
    ids=[
        "invalid-uri",
        "scheme-only",
        "malformed-ipv6",
        "https-no-host",
        "wildcard",
        "fragment",
        "http-non-localhost",
        "javascript-scheme",
        "javascript-scheme-mixed-case",
        "data-scheme",
        "file-scheme",
    ],
)
def test_validate_redirect_uri__invalid_input__raises_validation_error(
    uri: str,
    expected_message: str,
) -> None:
    # Given / When / Then
    with pytest.raises(ValidationError, match=expected_message):  # Then
        validate_redirect_uri(uri)


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/callback",
        "http://localhost:8080/callback",
        "claude://oauth/callback",
        "com.example.app:/oauth2redirect",
    ],
    ids=["https", "localhost", "custom-scheme", "reverse-domain"],
)
def test_validate_redirect_uri__valid_input__returns_uri(uri: str) -> None:
    # Given / When
    result = validate_redirect_uri(uri)

    # Then
    assert result == uri
