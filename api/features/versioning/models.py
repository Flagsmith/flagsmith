import datetime
import typing

from core.models import (
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from django.conf import settings
from django.db import models
from django.db.models import Index
from django.utils import timezone

from features.versioning.exceptions import FeatureVersioningError

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.models import Feature
    from users.models import FFAdminUser


class EnvironmentFeatureVersion(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    sha = models.CharField(primary_key=True, max_length=64)
    environment = models.ForeignKey(
        "environments.Environment", on_delete=models.CASCADE
    )
    feature = models.ForeignKey("features.Feature", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published = models.BooleanField(default=False)
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

    class Meta:
        indexes = [Index(fields=("environment", "feature"))]

    def __gt__(self, other):
        return self.is_live and (not other.is_live or self.live_from > other.live_from)

    @property
    def is_live(self) -> bool:
        return self.published and self.live_from <= timezone.now()

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
            environment=environment, feature=feature, published=True
        )

    def get_previous_version(self) -> typing.Optional["EnvironmentFeatureVersion"]:
        return (
            self.__class__.objects.filter(
                environment=self.environment,
                feature=self.feature,
                live_from__lt=timezone.now(),
                published=True,
            )
            .order_by("-live_from")
            .exclude(sha=self.sha)
            .first()
        )

    def publish(
        self, published_by: "FFAdminUser", live_from: datetime.datetime = None
    ) -> None:
        self.live_from = live_from or timezone.now()
        self.published = True
        self.published_by = published_by
