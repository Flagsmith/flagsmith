from audit.models import AuditLog
from environments.dynamodb import DynamoEnvironmentWrapper
from environments.models import Environment
from sse import (
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
)
from task_processor.decorators import register_task_handler


@register_task_handler()
def rebuild_environment_document(environment_id: int):
    wrapper = DynamoEnvironmentWrapper()
    if wrapper.is_enabled:
        environment = Environment.objects.get(id=environment_id)
        wrapper.write_environment(environment)


@register_task_handler()
def process_environment_update(audit_log_id: int):
    audit_log = AuditLog.objects.get(id=audit_log_id)

    # Send environment document to dynamodb
    Environment.write_environments_to_dynamodb(
        environment_id=audit_log.environment_id, project_id=audit_log.project_id
    )

    # send environment update message
    if audit_log.environment_id:
        send_environment_update_message_for_environment(audit_log.environment)
    else:
        send_environment_update_message_for_project(audit_log.project)
