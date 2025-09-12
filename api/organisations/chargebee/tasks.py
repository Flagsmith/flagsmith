from task_processor.decorators import (
    register_task_handler,
)

from organisations.chargebee.cache import ChargebeeCache


@register_task_handler()
def update_chargebee_cache():  # type: ignore[no-untyped-def]
    chargebee_cache = ChargebeeCache()  # type: ignore[no-untyped-call]
    chargebee_cache.refresh()  # type: ignore[no-untyped-call]
