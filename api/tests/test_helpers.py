from importlib import reload
from types import ModuleType
from typing import Any

from django.urls import URLResolver, clear_url_caches, get_resolver
from flag_engine.segments.types import ConditionOperator


def reload_urlconf() -> None:
    """Re-import every URL module, children first, so that routes gated on
    deployment flags at import time are re-evaluated."""
    reloaded: set[str] = set()

    def reload_resolver_modules(resolver: URLResolver) -> None:
        for url_pattern in resolver.url_patterns:
            if isinstance(url_pattern, URLResolver):
                reload_resolver_modules(url_pattern)
        if (
            isinstance(module := resolver.urlconf_module, ModuleType)
            and module.__name__ not in reloaded
        ):
            reloaded.add(module.__name__)
            reload(module)

    reload_resolver_modules(get_resolver())
    clear_url_caches()


def generate_segment_data(
    segment_name: str,
    project_id: int,
    condition_tuples: list[tuple[str, ConditionOperator, str]],
) -> dict[str, Any]:
    return {
        "name": segment_name,
        "project": project_id,
        "rules": [
            {
                "type": "ALL",
                "rules": [
                    {
                        "type": "ANY",
                        "rules": [],
                        "conditions": [
                            {
                                "property": condition_tuple[0],
                                "operator": condition_tuple[1],
                                "value": condition_tuple[2],
                            }
                            for condition_tuple in condition_tuples
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }
