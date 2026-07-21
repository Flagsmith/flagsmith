from typing import Any, Dict, Generator

from django.conf import settings
from django.core.cache import caches

from organisations.chargebee.client import chargebee_client
from organisations.chargebee.metadata import ChargebeeItem, ChargebeeObjMetadata

CHARGEBEE_CACHE_KEY = "chargebee_items"


class ChargebeeCache:
    def __init__(self):  # type: ignore[no-untyped-def]
        self._cache = caches[settings.CHARGEBEE_CACHE_LOCATION]

    def refresh(self):  # type: ignore[no-untyped-def]
        plans = self.fetch_plans()
        addons = self.fetch_addons()
        self._cache.set(CHARGEBEE_CACHE_KEY, {"plans": plans, "addons": addons})

    @property
    def plans(self) -> Dict[str, ChargebeeObjMetadata]:
        return self._get_items()["plans"]  # type: ignore[no-any-return]

    @property
    def addons(self) -> Dict[str, ChargebeeObjMetadata]:
        return self._get_items()["addons"]  # type: ignore[no-any-return]

    def _get_items(self) -> dict:  # type: ignore[type-arg]
        chargebee_items = self._cache.get(CHARGEBEE_CACHE_KEY)
        if chargebee_items is None:
            self.refresh()  # type: ignore[no-untyped-call]
        return self._cache.get(CHARGEBEE_CACHE_KEY)  # type: ignore[no-any-return]

    def fetch_plans(self) -> dict:  # type: ignore[type-arg]
        plans = {}
        for entry in get_item_generator(ChargebeeItem.PLAN):
            plan = entry.plan
            plan_metadata = plan.meta_data or {}
            plans[plan.id] = ChargebeeObjMetadata(**plan_metadata)
        return plans

    def fetch_addons(self) -> dict:  # type: ignore[type-arg]
        addons = {}
        for entry in get_item_generator(ChargebeeItem.ADDON):
            addon = entry.addon
            addon_metadata = addon.meta_data or {}
            addons[addon.id] = ChargebeeObjMetadata(**addon_metadata)
        return addons


def get_item_generator(item: ChargebeeItem) -> Generator[Any, None, None]:
    next_offset = None
    while True:
        resource = getattr(chargebee_client, item.value)
        list_params_cls = resource.ListParams
        entries = resource.list(list_params_cls(limit=100, offset=next_offset))
        for entry in entries.list:
            yield entry

        if entries.next_offset:
            next_offset = entries.next_offset
            continue

        break
