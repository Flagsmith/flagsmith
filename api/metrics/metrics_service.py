from typing import Any, Dict, List, Mapping
from metrics.types import MetricDefinition, MetricItemPayload

def build_metrics_section(
    data: Dict[str, Any],
    definition: Mapping[str, MetricDefinition]
) -> List[MetricItemPayload]:
    section: List[MetricItemPayload] = []
    for key, meta in definition.items():
        if key not in data or meta.get("disabled", False) is True:
            continue
        section.append({
            "title": meta.get("title", key),
            "description": meta.get("description", key),
            "value": data[key],
        })
    return section
