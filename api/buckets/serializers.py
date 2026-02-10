from rest_framework import serializers

from buckets.models import Bucket


class BucketQuerySerializer(serializers.Serializer):
    """Query parameters for bucket list endpoint"""

    search = serializers.CharField(required=False, help_text="Search buckets by name")
    sort_field = serializers.ChoiceField(
        choices=("created_date", "name"),
        default="created_date",
        help_text="Field to sort by",
    )
    sort_direction = serializers.ChoiceField(
        choices=("ASC", "DESC"),
        default="ASC",
        help_text="Sort direction (ascending or descending)",
    )


class BucketSerializer(serializers.ModelSerializer):
    """
    Main serializer for Bucket CRUD operations.
    """

    feature_count = serializers.SerializerMethodField(
        read_only=True, help_text="Number of features in this bucket"
    )

    class Meta:
        model = Bucket
        fields = (
            "id",
            "uuid",
            "name",
            "description",
            "created_date",
            "project",
            "feature_count",
        )
        read_only_fields = ("id", "uuid", "created_date", "project", "feature_count")

    def get_feature_count(self, obj):
        """Return count of features in this bucket"""
        return obj.features.count()

    def validate_name(self, name):
        """Validate bucket name uniqueness within project (case-insensitive)"""
        view = self.context.get("view")
        if not view:
            return name

        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return name

        unique_filters = {
            "project__id": project_pk,
            "name__iexact": name,
        }

        existing_queryset = Bucket.objects.filter(**unique_filters)
        if self.instance:
            existing_queryset = existing_queryset.exclude(id=self.instance.id)

        if existing_queryset.exists():
            raise serializers.ValidationError(
                "Bucket with that name already exists for this project. "
                "Note that bucket names are case insensitive."
            )

        return name


class CreateBucketSerializer(BucketSerializer):
    """Serializer for creating buckets"""

    pass


class UpdateBucketSerializer(BucketSerializer):
    """Serializer for updating buckets"""

    class Meta(BucketSerializer.Meta):
        # Name can be updated, but project cannot be changed
        read_only_fields = ("id", "uuid", "created_date", "project", "feature_count")


class BucketMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for nested representations (e.g., in Feature serializer).
    """

    class Meta:
        model = Bucket
        fields = ("id", "uuid", "name")
        read_only_fields = ("id", "uuid", "name")
