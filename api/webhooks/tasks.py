from task_processor.decorators import (
    register_task_handler,
)

from webhooks.webhooks import (
    call_environment_webhooks as call_environment_webhooks_service,
)
from webhooks.webhooks import (
    call_organisation_webhooks as call_organisation_webhooks_service,
)
from webhooks.webhooks import (
    call_webhook_with_failure_mail_after_retries as call_webhook_with_failure_mail_after_retries_service,
)

call_environment_webhooks = register_task_handler()(
    call_environment_webhooks_service,
)

call_organisation_webhooks = register_task_handler()(
    call_organisation_webhooks_service,
)

call_webhook_with_failure_mail_after_retries = register_task_handler()(
    call_webhook_with_failure_mail_after_retries_service,
)
