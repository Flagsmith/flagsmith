from audit.models import AuditLog
from environments.dynamodb import (
    DynamoEnvironmentWrapper,
    DynamoIdentityWrapper,
)
from environments.models import (
    Environment,
    environment_v2_wrapper,
    environment_wrapper,
)
from sse import (
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
)
from task_processor.decorators import register_task_handler
from task_processor.models import TaskPriority


@register_task_handler(priority=TaskPriority.HIGH)
def rebuild_environment_document(environment_id: int):
    wrapper = DynamoEnvironmentWrapper()
    if wrapper.is_enabled:
        environment = Environment.objects.get(id=environment_id)
        wrapper.write_environment(environment)


@register_task_handler(priority=TaskPriority.HIGHEST)
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


@register_task_handler()
def delete_environment_from_dynamo(api_key: str, environment_id: str):
    # Delete environment
    environment_wrapper.delete_environment(api_key)

    # Delete identities
    identity_wrapper = DynamoIdentityWrapper()
    identity_wrapper.delete_all_identities(api_key)

    # Delete environment_v2 documents
    environment_v2_wrapper.delete_environment(environment_id)


@register_task_handler()
def delete_environment(environment_id: int) -> None:
    Environment.objects.get(id=environment_id).delete()
