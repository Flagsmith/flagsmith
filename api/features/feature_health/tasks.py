from task_processor.decorators import (
    register_task_handler,
)

from features.feature_health import services
from features.models import Feature


@register_task_handler()
def update_feature_unhealthy_tag(
    feature_id: int,
    environment_ids: list[int | None] | None = None,
) -> None:
    if feature := Feature.objects.filter(id=feature_id).first():
        services.update_feature_unhealthy_tag(feature)
        services.send_feature_health_updated(
            feature,
            # Tasks enqueued before `environment_ids` was added don't carry it;
            # treat them as not tied to an environment.
            environment_ids if environment_ids is not None else [None],
        )
