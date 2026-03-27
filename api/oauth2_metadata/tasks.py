from datetime import timedelta

from task_processor.decorators import register_recurring_task


@register_recurring_task(run_every=timedelta(hours=24))
def clear_expired_oauth2_tokens() -> None:
    from django.core.management import call_command

    call_command("cleartokens")
