from task_processor.decorators import register_task_handler  # type: ignore[import-untyped]

from features.feature_health import services
from features.models import Feature


@register_task_handler()  # type: ignore[misc]
def update_feature_unhealthy_tag(feature_id: int) -> None:
    if feature := Feature.objects.filter(id=feature_id).first():
        services.update_feature_unhealthy_tag(feature)
