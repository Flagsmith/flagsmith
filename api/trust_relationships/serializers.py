from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from trust_relationships.models import TrustRelationship
from trust_relationships.services import (
    create_trust_relationship,
    update_trust_relationship,
)
from trust_relationships.types import ClaimRule


class TokenExchangeRequestSerializer(serializers.Serializer[None]):
    token = serializers.CharField(
        help_text="An OIDC token issued by a trusted identity provider, "
        "e.g. a GitHub Actions job token.",
    )


class TokenExchangeResponseSerializer(serializers.Serializer[dict[str, Any]]):
    access_token = serializers.CharField(
        help_text="Short-lived access token for the Admin API.",
    )
    token_type = serializers.CharField(help_text='Always "Bearer".')
    expires_in = serializers.IntegerField(
        help_text="Access token lifetime in seconds.",
    )


class ClaimRuleSerializer(serializers.Serializer[ClaimRule]):
    claim = serializers.CharField(max_length=255)
    values = serializers.ListField(
        child=serializers.CharField(max_length=500),
        min_length=1,
    )


class TrustRelationshipSerializer(serializers.ModelSerializer[TrustRelationship]):
    # Deliberately required: an omitted `is_admin` on a full update would
    # otherwise silently escalate a non-admin trust relationship to admin.
    is_admin = serializers.BooleanField()
    claim_rules = ClaimRuleSerializer(many=True, required=False)
    master_api_key_id = serializers.CharField(read_only=True)
    master_api_key_prefix = serializers.CharField(
        source="master_api_key.prefix", read_only=True
    )

    class Meta:
        model = TrustRelationship
        fields = (
            "id",
            "name",
            "issuer",
            "audience",
            "claim_rules",
            "is_admin",
            "master_api_key_id",
            "master_api_key_prefix",
            "created_at",
            "created_by",
        )
        read_only_fields = ("id", "created_at", "created_by")
        # Declared manually — since DRF 3.16 it can't auto-generate a validator
        # for `unique_live_issuer_audience`, whose condition is on `deleted_at`,
        # a field not writable here. `objects` excludes soft-deleted rows.
        # https://github.com/encode/django-rest-framework/pull/9360
        validators = [
            UniqueTogetherValidator(
                queryset=TrustRelationship.objects.all(),
                fields=("issuer", "audience"),
            )
        ]

    def validate_issuer(self, issuer: str) -> str:
        parsed = urlparse(issuer)
        if parsed.scheme != "https":
            raise serializers.ValidationError("Issuer must be an https:// URL.")
        if parsed.query or parsed.fragment:
            raise serializers.ValidationError(
                "Issuer must not contain a query string or fragment."
            )
        # Stored verbatim: OIDC matches `iss` by exact string, and issuers
        # such as Auth0's legitimately end in a slash. Discovery strips the
        # slash locally when building its URL.
        return issuer

    def validate_is_admin(self, is_admin: bool) -> bool:
        if is_admin is False and not settings.IS_RBAC_INSTALLED:
            raise serializers.ValidationError(
                "RBAC is not installed, cannot create non-admin trust relationship"
            )
        return is_admin

    def validate_claim_rules(self, claim_rules: list[ClaimRule]) -> list[ClaimRule]:
        # DRF yields OrderedDicts; store plain JSON.
        return [
            ClaimRule(claim=rule["claim"], values=rule["values"])
            for rule in claim_rules
        ]

    def create(self, validated_data: dict[str, Any]) -> TrustRelationship:
        validated_data.setdefault("claim_rules", [])
        return create_trust_relationship(**validated_data)

    def update(
        self, instance: TrustRelationship, validated_data: dict[str, Any]
    ) -> TrustRelationship:
        return update_trust_relationship(
            trust_relationship=instance,
            name=validated_data.get("name", instance.name),
            issuer=validated_data.get("issuer", instance.issuer),
            audience=validated_data.get("audience", instance.audience),
            is_admin=validated_data.get("is_admin", instance.is_admin),
            claim_rules=validated_data.get("claim_rules", instance.claim_rules),
        )
