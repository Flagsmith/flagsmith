from environment.models import Environment

from task_processor.decorators import register_task_handler

from .models import APIUsage, FeatureEvaluation, Resource
from .tracker import TRACKED_RESOURCE_ACTIONS


@register_task_handler()
def track_feature_evaluation(environment_id, feature_evaluations):
    for feature_id, evaluation_count in feature_evaluations.items():
        kwargs = {"feature_id": feature_id, "environment_id": environment_id}
        FeatureEvaluation.objects.create(**kwargs)


# TODO: improve this
def get_resource_enum(resource):
    {
        "flags": Resource.FLAGS,
        "identities": Resource.IDENTITIES,
        "traits": Resource.TRAITS,
        "environment_document": Resource.ENVIRONMENT_DOCUMENT,
    }.get(resource)


@register_task_handler()
def track_request(resource: str, host: str, environment_key: str):
    if resource and resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(environment_key)
        if environment is None:
            return
        APIUsage.objects.create(
            enviroment=environment,
            resource=get_resource_enum(resource),
            host=host,
        )
