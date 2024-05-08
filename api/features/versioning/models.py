import datetime
import typing
import uuid

from core.models import (
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from django.conf import settings
from django.db import models
from django.db.models import Index
from django.utils import timezone

from features.versioning.exceptions import FeatureVersioningError
from features.versioning.managers import EnvironmentFeatureVersionManager
from features.versioning.signals import environment_feature_version_published

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.models import Feature
    from users.models import FFAdminUser


class EnvironmentFeatureVersion(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(),
):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    environment = models.ForeignKey(
        "environments.Environment", on_delete=models.CASCADE
    )
    feature = models.ForeignKey("features.Feature", on_delete=models.CASCADE)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(blank=True, null=True)
    live_from = models.DateTimeField(null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="published_environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    change_request = models.ForeignKey(
        "workflows_core.ChangeRequest",
        related_name="environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    objects = EnvironmentFeatureVersionManager()

    class Meta:
        indexes = [Index(fields=("environment", "feature"))]
        ordering = ("-live_from",)

    def __gt__(self, other):
        return self.is_live and (not other.is_live or self.live_from > other.live_from)

    @property
    def is_live(self) -> bool:
        return self.published and self.live_from <= timezone.now()

    @property
    def published(self) -> bool:
        return self.published_at is not None

    @classmethod
    def create_initial_version(
        cls, environment: "Environment", feature: "Feature"
    ) -> "EnvironmentFeatureVersion":
        """
        Create an initial version with all the current feature states
        for a feature / environment combination.
        """

        if not environment.use_v2_feature_versioning:
            raise FeatureVersioningError(
                "Cannot create initial version for environment using v1 versioning."
            )
        elif cls.objects.filter(environment=environment, feature=feature).exists():
            raise FeatureVersioningError(
                "Version already exists for this feature / environment combination."
            )

        return cls.objects.create(
            environment=environment, feature=feature, published_at=timezone.now()
        )

    def get_previous_version(self) -> typing.Optional["EnvironmentFeatureVersion"]:
        return (
            self.__class__.objects.filter(
                environment=self.environment,
                feature=self.feature,
                live_from__lt=timezone.now(),
                published_at__isnull=False,
            )
            .order_by("-live_from")
            .exclude(uuid=self.uuid)
            .first()
        )

    def publish(
        self,
        published_by: "FFAdminUser",
        live_from: datetime.datetime = None,
        persist: bool = True,
    ) -> None:
        now = timezone.now()

        self.live_from = live_from or (self.live_from or now)
        self.published_at = now
        self.published_by = published_by
        if persist:
            self.save()
            environment_feature_version_published.send(self.__class__, instance=self)
