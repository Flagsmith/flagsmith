from organisations.chargebee.cache import ChargebeeCache
from task_processor.decorators import register_task_handler


@register_task_handler()
def update_chargebee_cache():
    chargebee_cache = ChargebeeCache()
    chargebee_cache.refresh()
