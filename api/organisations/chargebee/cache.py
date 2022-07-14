from datetime import datetime
from typing import Optional

import chargebee as chargebee

from .types import ChargebeeObjMetadata


class ChargebeeCache:
    def __init__(self):
        self.cache = {"plans": {}, "addons": {}}
        self.refreshed_at = None
        self.refresh()

    def refresh(self):
        self.refresh_plans()
        self.refresh_addons()
        self.refreshed_at = datetime.now()

    def get_plan_metadata(self, plan_id) -> Optional[ChargebeeObjMetadata]:
        return self.cache["plans"].get(plan_id)

    def get_addon_metadata(self, plan_id) -> Optional[ChargebeeObjMetadata]:
        return self.cache["addons"].get(plan_id)

    def refresh_plans(self):
        entries = chargebee.Plan.list(limit=100)
        while entries.next_offset:
            for entry in entries:
                plan = entry.plan
                plan_metadata = plan.meta_data or {}
                self.cache["plans"][plan.id] = ChargebeeObjMetadata(**plan_metadata)
            entries = chargebee.Plan.list(limit=100, offset=entries.next_offset)

    def refresh_addons(self):
        entries = chargebee.Addon.list(limit=100)
        while entries.next_offset:
            for entry in entries:
                addon = entry.addon
                addon_metadata = addon.meta_data or {}
                self.cache["addons"][addon.id] = ChargebeeObjMetadata(**addon_metadata)
            entries = chargebee.Addon.list(limit=100, offset=entries.next_offset)
