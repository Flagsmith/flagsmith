import pytest
from django.core.exceptions import ValidationError

from oauth2_metadata.services import validate_redirect_uri


@pytest.mark.parametrize(
    ("uri", "expected_message"),
    [
        ("not-a-uri", "Invalid URI"),
        ("https://*.example.com/callback", "Wildcards"),
    ],
    ids=["invalid-uri", "wildcard"],
)
def test_validate_redirect_uri__invalid_input__raises_validation_error(
    uri: str,
    expected_message: str,
) -> None:
    # Given / When / Then
    with pytest.raises(ValidationError, match=expected_message):  # Then
        validate_redirect_uri(uri)
