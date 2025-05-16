from typing import Callable

from metrics.constants import ALL_METRIC_DEFINITIONS
from metrics.types import EnvMetricsName, EnvMetricsPayload


def build_metrics(
    qs_map: dict[EnvMetricsName, tuple[Callable[[], int], Callable[[], bool] | None]],
) -> EnvMetricsPayload:
    metrics: EnvMetricsPayload = []

    for definition in ALL_METRIC_DEFINITIONS:
        name = definition["name"]
        entity = definition["entity"]
        base_disabled = definition.get("disabled", False)

        if name not in qs_map:
            continue

        count_fn, override_disabled_fn = qs_map[name]
        is_disabled = base_disabled
        if not base_disabled and override_disabled_fn is not None:
            is_disabled = not override_disabled_fn()

        if is_disabled:
            continue

        metrics.append(
            {
                **definition,
                "name": name.value,
                "entity": entity.value,
                "value": count_fn(),
            }
        )

    return sorted(metrics, key=lambda m: m.get("rank", 0))
