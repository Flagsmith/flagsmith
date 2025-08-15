from rest_framework import serializers

from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.code_references.types import (
    CodeReference,
    CodeReferencesRepositoryCount,
    FeatureFlagCodeReferences,
    VCSProvider,
)


class _BaseCodeReferenceSerializer(serializers.Serializer[CodeReference]):
    file_path = serializers.CharField(max_length=200)
    line_number = serializers.IntegerField(min_value=1)


class _CodeReferenceSubmitSerializer(_BaseCodeReferenceSerializer):
    feature_name = serializers.CharField(max_length=100)


class _CodeReferenceDetailSerializer(_BaseCodeReferenceSerializer):
    scanned_at = serializers.DateTimeField()
    vcs_provider = serializers.ChoiceField(choices=VCSProvider.choices)
    repository_url = serializers.URLField()
    revision = serializers.CharField()
    permalink = serializers.URLField()


class FeatureFlagCodeReferencesScanSerializer(
    serializers.ModelSerializer[FeatureFlagCodeReferencesScan],
):
    code_references = _CodeReferenceSubmitSerializer(
        many=True, required=True, allow_empty=False
    )

    class Meta:
        model = FeatureFlagCodeReferencesScan
        fields = [
            "created_at",
            "repository_url",
            "project",
            "revision",
            "code_references",
        ]
        read_only_fields = [
            "created_at",
            "project",
        ]


class FeatureFlagCodeReferencesSerializer(
    serializers.Serializer[FeatureFlagCodeReferences],
):
    first_scanned_at = serializers.DateTimeField()
    last_scanned_at = serializers.DateTimeField()

    code_references = _CodeReferenceDetailSerializer(many=True)

    class Meta:
        fields = read_only_fields = [
            "first_scanned_at",
            "last_scanned_at",
            "code_references",
        ]


class CodeReferencesRepositoryCountSerializer(
    serializers.Serializer[CodeReferencesRepositoryCount],
):
    repository_url = serializers.URLField()
    count = serializers.IntegerField()
