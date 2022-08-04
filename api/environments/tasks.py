from environments.dynamodb import DynamoEnvironmentWrapper
from environments.models import Environment
from task_processor.decorators import register_task_handler


@register_task_handler()
def rebuild_environment_document(environment_id: int):
    wrapper = DynamoEnvironmentWrapper()
    environment = Environment.objects.get(id=environment_id)
    wrapper.write_environment(environment)
