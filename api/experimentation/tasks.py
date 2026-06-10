from task_processor.decorators import register_task_handler

from experimentation import ingestion_sync_service


@register_task_handler()
def add_environment_key_to_ingestion(environment_api_key: str) -> None:
    ingestion_sync_service.set_environment_key(environment_api_key)


@register_task_handler()
def delete_environment_key_from_ingestion(environment_api_key: str) -> None:
    ingestion_sync_service.delete_environment_key(environment_api_key)
