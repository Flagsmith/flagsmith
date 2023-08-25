import logging
import typing

from django.utils import timezone

from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import (
    get_environment_flags_queryset,
)
from task_processor.decorators import register_task_handler

if typing.TYPE_CHECKING:
    from environments.models import Environment


logger = logging.getLogger(__name__)


@register_task_handler()
def enable_v2_versioning(environment_id: int):
    from environments.models import Environment

    environment = Environment.objects.get(id=environment_id)

    _create_initial_feature_versions(environment)

    environment.use_v2_feature_versioning = True
    environment.save()


def _create_initial_feature_versions(environment: "Environment"):
    from features.models import Feature

    for feature in Feature.objects.filter(project=environment.project_id):
        ef_version = EnvironmentFeatureVersion.objects.create(
            feature=feature,
            environment=environment,
            published=True,
            live_from=timezone.now(),
        )
        get_environment_flags_queryset(environment=environment).filter(
            identity__isnull=True, feature=feature
        ).update(environment_feature_version=ef_version)
