import typing

from django.conf import settings
from rest_framework import serializers

from environments.dynamodb.migrator import IdentityMigrator
from environments.dynamodb.types import ProjectIdentityMigrationStatus
from organisations.models import Subscription
from organisations.subscriptions.serializers.mixins import (
    ReadOnlyIfNotValidPlanMixin,
)
from permissions.serializers import CreateUpdateUserPermissionSerializerABC
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.serializers import UserListSerializer, UserPermissionGroupSerializer


class ProjectListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    migration_status = serializers.SerializerMethodField(
        help_text="Edge migration status of the project; can be one of: "
        + ", ".join([k.value for k in ProjectIdentityMigrationStatus])
    )
    use_edge_identities = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "uuid",
            "name",
            "organisation",
            "hide_disabled_flags",
            "enable_dynamo_db",
            "migration_status",
            "use_edge_identities",
            "prevent_flag_defaults",
            "enable_realtime_updates",
            "only_allow_lower_case_feature_names",
            "feature_name_regex",
            "show_edge_identity_overrides_for_feature",
            "stale_flags_limit_days",
            "edge_v2_migration_status",
            "minimum_change_request_approvals",
        )
        read_only_fields = (
            "enable_dynamo_db",
            "edge_v2_migration_status",
        )

    def get_migration_status(self, obj: Project) -> str:
        if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            migration_status = ProjectIdentityMigrationStatus.NOT_APPLICABLE.value
        elif obj.is_edge_project_by_default:
            migration_status = ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value
        else:
            migration_status = IdentityMigrator(obj.id).migration_status.value  # type: ignore[no-untyped-call]

        # Add migration status to the context - to be used by `get_use_edge_identities`
        self.context["migration_status"] = migration_status

        return migration_status

    def get_use_edge_identities(self, obj: Project) -> bool:
        return (  # type: ignore[no-any-return]
            self.context["migration_status"]
            == ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value
        )


class ProjectCreateSerializer(ReadOnlyIfNotValidPlanMixin, ProjectListSerializer):
    invalid_plans_regex = r"^(free|startup.*|scale-up.*)$"
    field_names = ("stale_flags_limit_days", "enable_realtime_updates")

    class Meta(ProjectListSerializer.Meta):
        validators = [
            serializers.UniqueTogetherValidator(  # type: ignore[attr-defined]
                queryset=ProjectListSerializer.Meta.model.objects.all(),
                fields=("name", "organisation"),
                message="A project with this name already exists.",
            )
        ]

    def get_subscription(self) -> typing.Optional[Subscription]:
        view = self.context["view"]

        if view.action == "create":
            # handle `organisation` not being part of the data
            # When request comes from yasg2 (as part of schema generation)
            organisation_id = view.request.data.get("organisation")
            if not organisation_id:
                return None

            # Organisation should only have a single subscription
            return Subscription.objects.filter(organisation_id=organisation_id).first()  # type: ignore[no-any-return]
        elif view.action in ("update", "partial_update"):
            # handle instance not being set
            # When request comes from yasg2 (as part of schema generation)
            if not self.instance:
                return None
            return getattr(self.instance.organisation, "subscription", None)  # type: ignore[union-attr]
        return None


class ProjectUpdateSerializer(ProjectCreateSerializer):
    class Meta(ProjectCreateSerializer.Meta):
        read_only_fields = ProjectCreateSerializer.Meta.read_only_fields + (  # type: ignore[assignment]
            "organisation",
        )


class ProjectRetrieveSerializer(ProjectListSerializer):
    total_features = serializers.SerializerMethodField()
    total_segments = serializers.SerializerMethodField()

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + (  # type: ignore[assignment]
            "max_segments_allowed",
            "max_features_allowed",
            "max_segment_overrides_allowed",
            "total_features",
            "total_segments",
        )

        read_only_fields = (  # type: ignore[assignment]
            "max_segments_allowed",
            "max_features_allowed",
            "max_segment_overrides_allowed",
            "total_features",
            "total_segments",
        )

    def get_total_features(self, instance: Project) -> int:
        # added here to prevent need for annotate(Count("features", distinct=True))
        # which causes performance issues.
        return instance.features.count()

    def get_total_segments(self, instance: Project) -> int:
        # added here to prevent need for annotate(Count("segments", distinct=True))
        # which causes performance issues.
        return instance.live_segment_count()


class CreateUpdateUserProjectPermissionSerializer(
    CreateUpdateUserPermissionSerializerABC
):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserProjectPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ("user",)  # type: ignore[assignment]


class ListUserProjectPermissionSerializer(CreateUpdateUserProjectPermissionSerializer):
    user = UserListSerializer()


class CreateUpdateUserPermissionGroupProjectPermissionSerializer(
    CreateUpdateUserPermissionSerializerABC
):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserPermissionGroupProjectPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ("group",)  # type: ignore[assignment]


class ListUserPermissionGroupProjectPermissionSerializer(
    CreateUpdateUserPermissionGroupProjectPermissionSerializer
):
    group = UserPermissionGroupSerializer()
