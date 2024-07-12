from task_processor.decorators import register_task_handler

from organisations.chargebee.cache import ChargebeeCache


@register_task_handler()
def update_chargebee_cache():
    chargebee_cache = ChargebeeCache()
    chargebee_cache.refresh()
