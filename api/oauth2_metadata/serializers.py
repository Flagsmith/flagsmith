import unicodedata

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from oauth2_metadata.services import validate_redirect_uri


class OAuthConsentSerializer(serializers.Serializer):  # type: ignore[type-arg]
    allow = serializers.BooleanField()
    client_id = serializers.CharField()
    redirect_uri = serializers.CharField()
    response_type = serializers.CharField()
    scope = serializers.CharField(required=False, default="mcp")
    code_challenge = serializers.CharField()
    code_challenge_method = serializers.CharField()
    state = serializers.CharField(required=False, allow_blank=True, default="")


# RFC 7591 § 2 places no constraints on `client_name`, and § 2.2 provides for localised names,
# Only protect against control and formatting characters breaking the layout
_DISALLOWED_CLIENT_NAME_CATEGORIES = frozenset(
    {"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"}
)

DEFAULT_CLIENT_NAME = "MCP client"

# Matches token_endpoint_auth_methods_supported in the RFC 8414 metadata.
TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]


class DCRRequestSerializer(serializers.Serializer[None]):
    # Optional per RFC 7591 §2; null, blank and absent all mean "unnamed".
    client_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=DEFAULT_CLIENT_NAME,
    )
    redirect_uris = serializers.ListField(
        child=serializers.CharField(max_length=2000),
        min_length=1,
        max_length=5,
        required=True,
    )
    grant_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=["authorization_code", "refresh_token"],
    )
    response_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=["code"],
    )
    token_endpoint_auth_method = serializers.ChoiceField(
        choices=TOKEN_ENDPOINT_AUTH_METHODS,
        required=False,
        default="none",
    )

    def validate_client_name(self, value: str | None) -> str:
        if not value or not (name := unicodedata.normalize("NFC", value.strip())):
            return DEFAULT_CLIENT_NAME
        if any(
            unicodedata.category(character) in _DISALLOWED_CLIENT_NAME_CATEGORIES
            for character in name
        ):
            raise serializers.ValidationError(
                "Client name may not contain control, formatting or separator "
                "characters."
            )
        return name

    def validate_redirect_uris(self, value: list[str]) -> list[str]:
        errors: list[str] = []
        for uri in value:
            try:
                validate_redirect_uri(uri)
            except DjangoValidationError as e:
                errors.append(str(e.message))
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate_grant_types(self, value: list[str]) -> list[str]:
        allowed = {"authorization_code", "refresh_token"}
        invalid = set(value) - allowed
        if invalid:
            raise serializers.ValidationError(
                f"Unsupported grant types: {', '.join(sorted(invalid))}"
            )
        return value

    def validate_response_types(self, value: list[str]) -> list[str]:
        allowed = {"code"}
        invalid = set(value) - allowed
        if invalid:
            raise serializers.ValidationError(
                f"Unsupported response types: {', '.join(sorted(invalid))}"
            )
        return value
