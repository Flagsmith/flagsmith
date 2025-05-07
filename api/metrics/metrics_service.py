from metrics.types import EnvMetricsPayload, EnvMetricsName
from metrics.constants import ALL_METRIC_DEFINITIONS
from typing import Callable

def build_metrics(qs_map: dict[EnvMetricsName, Callable[[], int]]) -> EnvMetricsPayload:
    metrics: EnvMetricsPayload = []

    for definition in ALL_METRIC_DEFINITIONS:
        if definition.get("disabled"):
            continue

        fn = qs_map.get(definition["name"])
        if fn is None:
            continue

        metrics.append({
            **definition,
            "name": definition["name"].value,
            "entity": definition["entity"].value,
            "value": fn(),
        })

    return sorted(metrics, key=lambda m: m.get("rank", 0))