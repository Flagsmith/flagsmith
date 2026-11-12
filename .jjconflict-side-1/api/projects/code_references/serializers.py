from rest_framework import serializers

from projects.code_references.constants import MAX_FILE_PATH_LENGTH
from projects.code_references.types import (
    CodeReference,
    CodeReferencesRepositoryCount,
    FeatureFlagCodeReferencesRepositorySummary,
    FeatureFlagCodeReferencesScan,
    VCSProvider,
)


class _BaseCodeReferenceSerializer(serializers.Serializer[CodeReference]):
    file_path = serializers.CharField(max_length=MAX_FILE_PATH_LENGTH)
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
    serializers.Serializer[FeatureFlagCodeReferencesScan],
):
    created_at = serializers.DateTimeField(read_only=True)
    project = serializers.IntegerField(read_only=True, source="project.id")
    repository_url = serializers.URLField()
    vcs_provider = serializers.ChoiceField(
        choices=VCSProvider.choices,
        default=VCSProvider.GITHUB,
    )
    revision = serializers.CharField(max_length=100)
    code_references = _CodeReferenceSubmitSerializer(many=True, required=True)


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
