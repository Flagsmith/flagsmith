import copy
import datetime
import hashlib
import time
import typing
import uuid

from django.db import models
from django.db.models import Index
from django.utils import timezone
from django_lifecycle import AFTER_CREATE, BEFORE_CREATE, LifecycleModel, hook

from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.exceptions import FeatureVersioningError


class EnvironmentFeatureVersion(LifecycleModel):
    # TODO:
    #  - verify that sha can be used as primary key in oracle / mysql
    #  - are there any performance impacts to consider with such a large primary key?
    sha = models.CharField(primary_key=True, max_length=64)
    environment = models.ForeignKey(
        "environments.Environment", on_delete=models.CASCADE
    )
    feature = models.ForeignKey("features.Feature", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published = models.BooleanField(default=False)
    live_from = models.DateTimeField(null=True)

    class Meta:
        indexes = [Index(fields=("environment", "feature"))]

    def __gt__(self, other):
        return self.is_live and (not other.is_live or self.live_from > other.live_from)

    @hook(AFTER_CREATE)
    def add_existing_feature_states(self):
        previous_environment_feature_version = self.get_previous_version()
        if not previous_environment_feature_version:
            return

        feature_states = []
        for feature_state in previous_environment_feature_version.feature_states.all():
            new_feature_state = copy.deepcopy(feature_state)
            new_feature_state.id = None
            new_feature_state.environment_feature_version = self
            new_feature_state.uuid = uuid.uuid4()
            feature_states.append(new_feature_state)

        FeatureState.objects.bulk_create(feature_states)

    @hook(BEFORE_CREATE)
    def generate_sha(self):
        self.sha = hashlib.sha256(
            f"{self.environment.id}{self.feature.id}{time.time()}".encode("utf-8")
        ).hexdigest()

    @hook(BEFORE_CREATE, when="published", is_now=True)
    def update_live_from(self):
        if not self.live_from:
            self.live_from = timezone.now()

    @property
    def is_live(self):
        return self.published and self.live_from < timezone.now()

    @classmethod
    def create_initial_version(
        cls, environment: Environment, feature: Feature
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

    def publish(self, live_from: datetime.datetime = None) -> None:
        self.live_from = live_from or timezone.now()
        self.published = True
