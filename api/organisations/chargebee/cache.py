import chargebee as chargebee
from django.conf import settings
from django.core.cache import caches

from .types import ChargebeeItem, ChargebeeObjMetadata

CHARGEBEE_CACHE_KEY = "chargebee_items"


class ChargebeeCache:
    def __init__(self):
        self._cache = caches[settings.CHARGEBEE_CACHE_LOCATION]

    def refresh(self):
        plans = self.fetch_plans()
        addons = self.fetch_addons()
        self._cache.set(CHARGEBEE_CACHE_KEY, {"plans": plans, "addons": addons})

    @property
    def plans(self):
        return self._get_items()["plans"]

    @property
    def addons(self):
        return self._get_items()["addons"]

    def _get_items(self):
        chargebee_items = self._cache.get(CHARGEBEE_CACHE_KEY)
        if chargebee_items is None:
            self.refresh()
        return self._cache.get(CHARGEBEE_CACHE_KEY)

    def fetch_plans(self) -> dict:
        plans = {}
        for entry in get_item_generator(ChargebeeItem.PLAN):
            plan = entry.plan
            plan_metadata = plan.meta_data or {}
            plans[plan.id] = ChargebeeObjMetadata(**plan_metadata)
        return plans

    def fetch_addons(self) -> dict:
        addons = {}
        for entry in get_item_generator(ChargebeeItem.ADDON):
            addon = entry.addon
            addon_metadata = addon.meta_data or {}
            addons[addon.id] = ChargebeeObjMetadata(**addon_metadata)
        return addons


def get_item_generator(item: ChargebeeItem):
    next_offset = None
    while True:
        entries = getattr(chargebee, item.value).list(
            {"limit": 100, "offset": next_offset}
        )
        for entry in entries:
            yield entry

        if entries.next_offset:
            next_offset = entries.next_offset
            continue

        break
