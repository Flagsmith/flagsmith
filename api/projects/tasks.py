from decimal import Decimal

from django.conf import settings
from django.db import transaction

from task_processor.decorators import register_task_handler


@register_task_handler()
def write_environments_to_dynamodb(project_id: int) -> None:
    from environments.models import Environment

    Environment.write_environments_to_dynamodb(project_id=project_id)


@register_task_handler()
def migrate_project_environments_to_v2(project_id: int) -> None:
    from environments.dynamodb.services import migrate_environments_to_v2
    from projects.models import Project

    with transaction.atomic():
        project = Project.objects.select_for_update().get(id=project_id)

        if (capacity_budget := project.edge_v2_migration_read_capacity_budget) is None:
            capacity_budget = settings.EDGE_V2_MIGRATION_READ_CAPACITY_BUDGET

        if result := migrate_environments_to_v2(
            project_id=project_id,
            capacity_budget=Decimal(capacity_budget),
        ):
            project.edge_v2_migration_status = result.status
            project.save()


@register_task_handler()
def handle_cascade_delete(project_id: int) -> None:
    """
    Due to the combination of soft deletes and audit log functionality,
    cascade deletes for a project can take a long time for large projects.
    This task delegates the cascade delete to tasks for the main related
    entities for a project.
    """

    from environments.tasks import delete_environment
    from features.tasks import delete_feature
    from projects.models import Project
    from segments.tasks import delete_segment

    project = Project.objects.all_with_deleted().get(id=project_id)

    for environment_id in project.environments.values_list("id", flat=True):
        delete_environment.delay(kwargs={"environment_id": environment_id})

    for segment_id in project.segments.values_list("id", flat=True):
        delete_segment.delay(kwargs={"segment_id": segment_id})

    for feature_id in project.features.values_list("id", flat=True):
        delete_feature.delay(kwargs={"feature_id": feature_id})
