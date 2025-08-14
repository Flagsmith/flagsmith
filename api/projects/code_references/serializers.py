from typing import TypedDict

from rest_framework import serializers

from projects.code_references.models import FeatureFlagCodeReferencesScan


class _CodeReference(TypedDict):
    feature_name: str
    file_path: str
    line_number: int


class _CodeReferenceSerializer(serializers.Serializer[_CodeReference]):
    feature_name = serializers.CharField(max_length=100)
    file_path = serializers.CharField(max_length=200)
    line_number = serializers.IntegerField(min_value=1)


class FeatureFlagCodeReferencesScanSerializer(
    serializers.ModelSerializer[FeatureFlagCodeReferencesScan],
):
    code_references = _CodeReferenceSerializer(
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
