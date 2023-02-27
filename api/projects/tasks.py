from task_processor.decorators import register_task_handler


@register_task_handler()
def write_environments_to_dynamodb(project_id: int):
    from environments.models import Environment

    Environment.write_environments_to_dynamodb(project_id=project_id)
