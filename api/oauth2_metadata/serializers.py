import re

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from oauth2_metadata.services import validate_redirect_uri

# Allow letters, digits, spaces, hyphens, underscores, dots, and parentheses.
_CLIENT_NAME_RE = re.compile(r"^[\w\s.\-()]+$", re.UNICODE)


class DCRRequestSerializer(serializers.Serializer[None]):
    client_name = serializers.CharField(max_length=255, required=True)
    redirect_uris = serializers.ListField(
        child=serializers.URLField(),
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
    token_endpoint_auth_method = serializers.CharField(
        required=False,
        default="none",
    )

    def validate_client_name(self, value: str) -> str:
        if not _CLIENT_NAME_RE.match(value):
            raise serializers.ValidationError(
                "Client name may only contain letters, digits, spaces, "
                "hyphens, underscores, dots, and parentheses."
            )
        return value

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

    def validate_token_endpoint_auth_method(self, value: str) -> str:
        if value != "none":
            raise serializers.ValidationError(
                "Only public clients are supported; "
                "token_endpoint_auth_method must be 'none'."
            )
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
