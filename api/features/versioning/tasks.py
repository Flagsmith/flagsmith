from django.utils import timezone

from features.versioning.models import EnvironmentFeatureVersion
from task_processor.decorators import register_task_handler


@register_task_handler()
def create_initial_feature_versions(environment_id: int):
    from environments.models import Environment
    from features.models import Feature, FeatureState

    environment = Environment.objects.get(id=environment_id)
    assert environment.use_v2_feature_versioning

    for feature in Feature.objects.filter(project=environment.project_id):
        ef_version = EnvironmentFeatureVersion.objects.create(
            feature=feature,
            environment=environment,
            published=True,
            live_from=timezone.now(),
        )
        FeatureState.objects.filter(
            feature=feature, environment=environment, identity__isnull=True
        ).update(environment_feature_version=ef_version)
