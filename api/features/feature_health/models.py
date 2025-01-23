import typing

from core.models import (
    AbstractBaseExportableModel,
    abstract_base_auditable_model_factory,
)
from django.db import models
from django_lifecycle import AFTER_CREATE, LifecycleModelMixin, hook

from audit.related_object_type import RelatedObjectType
from features.feature_health.constants import (
    FEATURE_HEALTH_EVENT_CREATED_FOR_ENVIRONMENT_MESSAGE,
    FEATURE_HEALTH_EVENT_CREATED_MESSAGE,
    FEATURE_HEALTH_EVENT_CREATED_PROVIDER_MESSAGE,
    FEATURE_HEALTH_EVENT_CREATED_REASON_MESSAGE,
    FEATURE_HEALTH_PROVIDER_CREATED_MESSAGE,
    FEATURE_HEALTH_PROVIDER_DELETED_MESSAGE,
)

if typing.TYPE_CHECKING:
    from features.models import Feature
    from projects.models import Project
    from users.models import FFAdminUser


class FeatureHealthProviderName(models.Choices):
    SAMPLE = "Sample"
    GRAFANA = "Grafana"


class FeatureHealthEventType(models.Choices):
    UNHEALTHY = "UNHEALTHY"
    HEALTHY = "HEALTHY"


class FeatureHealthProvider(
    AbstractBaseExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    name = models.CharField(max_length=50, choices=FeatureHealthProviderName.choices)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE)
    created_by = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("type", "project")

    def get_create_log_message(
        self,
        history_instance: "FeatureHealthProvider",
    ) -> str | None:
        return FEATURE_HEALTH_PROVIDER_CREATED_MESSAGE % (self.type, self.project.name)

    def get_delete_log_message(
        self,
        history_instance: "FeatureHealthProvider",
    ) -> str | None:
        return FEATURE_HEALTH_PROVIDER_DELETED_MESSAGE % (self.type, self.project.name)

    def get_audit_log_author(
        self,
        history_instance: "FeatureHealthProvider",
    ) -> "FFAdminUser | None":
        return self.created_by


class FeatureHealthEventManager(models.Manager):
    def get_latest_by_feature(
        self,
        feature: "Feature",
    ) -> "models.QuerySet[FeatureHealthEvent]":
        return (
            self.filter(feature=feature)
            .order_by("provider_name", "-created_at")
            .distinct("provider_name")
        )

    def get_latest_by_project(
        self,
        project: "Project",
    ) -> "models.QuerySet[FeatureHealthEvent]":
        return (
            self.filter(feature__project=project)
            .order_by("provider_name", "feature_id", "-created_at")
            .distinct("provider_name", "feature_id")
        )


class FeatureHealthEvent(
    LifecycleModelMixin,
    AbstractBaseExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    """
    Holds the events that are generated when a feature health is changed.
    """

    related_object_type = RelatedObjectType.FEATURE_HEALTH

    objects: FeatureHealthEventManager = FeatureHealthEventManager()

    feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
        related_name="feature_health_events",
    )
    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="feature_health_events",
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=FeatureHealthEventType.choices)
    provider_name = models.CharField(max_length=255, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    @hook(AFTER_CREATE)
    def set_feature_health_tag(self):
        from features.feature_health.tasks import update_feature_unhealthy_tag

        update_feature_unhealthy_tag.delay(args=(self.feature.id,))

    def get_create_log_message(
        self,
        history_instance: "FeatureHealthEvent",
    ) -> str | None:
        if self.environment:
            message = FEATURE_HEALTH_EVENT_CREATED_FOR_ENVIRONMENT_MESSAGE % (
                self.type,
                self.feature.name,
                self.environment.name,
            )
        else:
            message = FEATURE_HEALTH_EVENT_CREATED_MESSAGE % (
                self.type,
                self.feature.name,
            )
        if self.provider_name:
            message += (
                FEATURE_HEALTH_EVENT_CREATED_PROVIDER_MESSAGE % self.provider_name
            )
        if self.reason:
            message += FEATURE_HEALTH_EVENT_CREATED_REASON_MESSAGE % self.reason
        return message
