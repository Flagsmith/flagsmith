from rest_framework import serializers

from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.code_references.types import (
    CodeReference,
    CodeReferencesRepositoryCount,
    FeatureFlagCodeReferencesRepositorySummary,
    VCSProvider,
)


class _BaseCodeReferenceSerializer(serializers.Serializer[CodeReference]):
    file_path = serializers.CharField(max_length=260)  # Windows' MAX_PATH
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


class FeatureFlagCodeReferencesRepositorySummarySerializer(
    serializers.Serializer[FeatureFlagCodeReferencesRepositorySummary],
):
    repository_url = serializers.URLField()
    vcs_provider = serializers.ChoiceField(choices=VCSProvider.choices)
    revision = serializers.CharField()
    last_successful_repository_scanned_at = serializers.DateTimeField()
    last_feature_found_at = serializers.DateTimeField(allow_null=True)
    code_references = _CodeReferenceDetailSerializer(many=True)


class FeatureFlagCodeReferencesRepositoryCountSerializer(
    serializers.Serializer[CodeReferencesRepositoryCount],
):
    repository_url = serializers.URLField()
    count = serializers.IntegerField()
    last_successful_repository_scanned_at = serializers.DateTimeField()
    last_feature_found_at = serializers.DateTimeField(allow_null=True)
