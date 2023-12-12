from django.db import transaction

from task_processor.decorators import register_task_handler


@register_task_handler()
def write_environments_to_dynamodb(project_id: int) -> None:
    from environments.models import Environment

    Environment.write_environments_to_dynamodb(project_id=project_id)


@register_task_handler()
def migrate_project_environments_to_v2(project_id: int) -> None:
    from environments.dynamodb.services import migrate_environments_to_v2
    from projects.models import IdentityOverridesV2MigrationStatus, Project

    with transaction.atomic():
        project = Project.objects.select_for_update().get(id=project_id)
        if migrate_environments_to_v2(project_id=project_id):
            project.identity_overrides_v2_migration_status = (
                IdentityOverridesV2MigrationStatus.COMPLETE
            )
            project.save()
