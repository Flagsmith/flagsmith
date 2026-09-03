"""
Per-metric slot builder for the experimentation results ClickHouse query.

Each _MetricSlot owns one alias (``m{i}``) and derives all three things that
must agree on it:
  - the per-identity expression in the unit_values CTE SELECT
  - the outer sufficient-stat aggregate in the final SELECT
  - the column pair read back from a result row by name during decode

ResultsQueryBuilder owns the slots and provides build_query() + decode_rows().
Because decode_rows looks each column up by name, the SELECT and the decode
bind on the alias rather than on column order — a reordered or inserted column
can't silently misalign them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from experimentation.constants import EXPOSURE_EVENT_NAME
from experimentation.dataclasses import ConversionBucket, MetricSpec
from experimentation.models import MetricAggregation
from experimentation.stats import VariantStats

_FLOAT_VALUE = "toFloat64OrZero(m.value)"

# Events are delivered at-least-once, so dedup keeps duplicates from inflating
# counts. Shared by the exposures, results and conversions queries.
_EXPOSURES_CTE = """
WITH exposures AS (
    SELECT
        identifier,
        if(uniqExact(value) > 1, '', any(value)) AS variant,
        uniqExact(value) > 1 AS quarantined,
        min(timestamp) AS first_exposure
    FROM events
    WHERE environment_key = %(environment_key)s
        AND event = %(exposure_event)s
        AND feature_name = %(feature_name)s
        AND timestamp >= %(window_start)s
        AND timestamp < %(window_end)s
    GROUP BY identifier
)"""

_EXPOSURES_COUNT_ONLY_QUERY = (
    _EXPOSURES_CTE
    + """
SELECT variant, count() AS n
FROM exposures
WHERE quarantined = 0
GROUP BY variant"""
)


def exposure_window_params(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
) -> dict[str, object]:
    """The parameters ``_EXPOSURES_CTE`` binds, for every query that starts
    from it."""
    return {
        "environment_key": environment_key,
        "exposure_event": EXPOSURE_EVENT_NAME,
        "feature_name": feature_name,
        "window_start": window_start,
        "window_end": window_end,
    }


def _metric_join(events_param: str) -> str:
    """Join each exposed identity to its metric events. ``events_param`` names
    the bound list of event names, so a query can join only the events it
    aggregates."""
    return f"""    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = %(environment_key)s
        AND m.event IN %({events_param})s
        AND m.timestamp >= %(window_start)s
        AND m.timestamp < %(window_end)s"""


@dataclass(frozen=True)
class _MetricSlot:
    """SQL column fragments for one metric in the results query.

    Keeps unit_select, outer_select, and decode co-located so that adding
    a new aggregation type or changing the column shape is a single edit.
    """

    spec: MetricSpec
    index: int

    @property
    def _alias(self) -> str:
        return f"m{self.index}"

    def _condition(self) -> str:
        # Post-exposure attribution lives in conditional aggregation, not JOIN ON:
        # ClickHouse 24.8 rejects ON clauses mixing left+right columns in an
        # inequality (error 403).
        return (
            f"m.event = %(metric_{self.index}_event)s"
            f" AND m.timestamp >= e.first_exposure"
        )

    def unit_select(self) -> str:
        """Per-identity expression for the unit_values CTE SELECT."""
        cond = self._condition()
        agg = self.spec.aggregation
        if agg == MetricAggregation.OCCURRENCE:
            return f"countIf({cond}) > 0 AS {self._alias}"
        if agg == MetricAggregation.COUNT:
            return f"countIf({cond}) AS {self._alias}"
        if agg == MetricAggregation.SUM:
            return f"sumIf({_FLOAT_VALUE}, {cond}) AS {self._alias}"
        if agg == MetricAggregation.MEAN:
            return (
                f"if(countIf({cond}) > 0, avgIf({_FLOAT_VALUE}, {cond}), 0)"
                f" AS {self._alias}"
            )
        raise ValueError(f"Unsupported metric aggregation: {agg}")

    def outer_select(self) -> str:
        """Sufficient-stat aggregates for the final SELECT."""
        a = self._alias
        return f"sum({a}) AS {a}_sum, sum({a} * {a}) AS {a}_sum_squares"

    @property
    def conversion_alias(self) -> str:
        return f"c{self.index}"

    def first_conversion_select(self) -> str | None:
        """Per-identity timestamp of the first post-exposure conversion, NULL
        when the identity never converted. Same attribution condition as
        unit_select, so bucket totals add up to the metric's ``sum``.

        None for value metrics: a count or sum accrues per event rather than
        once per identity, so a first-conversion timestamp can't chart it."""
        if self.spec.aggregation != MetricAggregation.OCCURRENCE:
            return None
        return (
            f"minIfOrNull(m.timestamp, {self._condition()}) AS {self.conversion_alias}"
        )

    def decode(self, n: int, row: Sequence[Any], index: dict[str, int]) -> VariantStats:
        """Read this slot's two columns (sum, sum_squares) from a row by name."""
        return VariantStats(
            n=n,
            sum=float(row[index[f"{self._alias}_sum"]]),
            sum_squares=float(row[index[f"{self._alias}_sum_squares"]]),
        )


class ResultsQueryBuilder:
    """Assembles and decodes the experimentation results ClickHouse query."""

    def __init__(self, specs: Sequence[MetricSpec]) -> None:
        self._slots = [_MetricSlot(spec, i) for i, spec in enumerate(specs)]

    def build_query(self) -> str:
        if not self._slots:
            return _EXPOSURES_COUNT_ONLY_QUERY

        unit_selects = ",\n        ".join(s.unit_select() for s in self._slots)
        outer_selects = ",\n    ".join(s.outer_select() for s in self._slots)

        return (
            _EXPOSURES_CTE
            + f""",
unit_values AS (
    SELECT
        e.variant AS variant,
        {unit_selects}
    FROM exposures AS e
{_metric_join("metric_events")}
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT variant, count() AS n,
    {outer_selects}
FROM unit_values
GROUP BY variant"""
        )

    def build_conversions_query(self, *, bucket_function: str) -> str | None:
        """Per variant and charted metric, how many identities first converted
        in each time bucket. None when no attached metric charts, since there
        is nothing to query."""
        slots = self._charted_slots
        if not slots:
            return None

        first_conversion_selects = ",\n        ".join(
            select for s in slots if (select := s.first_conversion_select())
        )
        indexes = ", ".join(str(s.index) for s in slots)
        aliases = ", ".join(s.conversion_alias for s in slots)

        return (
            _EXPOSURES_CTE
            + f""",
first_conversions AS (
    SELECT
        e.variant AS variant,
        {first_conversion_selects}
    FROM exposures AS e
{_metric_join("conversion_events")}
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT
    variant,
    metric_index,
    {bucket_function}(first_conversion, 'UTC') AS bucket,
    count() AS converted_identities
FROM first_conversions
ARRAY JOIN [{indexes}] AS metric_index, [{aliases}] AS first_conversion
WHERE first_conversion IS NOT NULL
GROUP BY variant, metric_index, bucket
ORDER BY bucket"""
        )

    @property
    def _charted_slots(self) -> list[_MetricSlot]:
        return [s for s in self._slots if s.first_conversion_select() is not None]

    def params(
        self,
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, object]:
        """Every parameter the results and conversions queries bind: the
        exposure window, each metric's event, and the event lists each join
        narrows to."""
        params = exposure_window_params(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
        )
        if not self._slots:
            return params
        params["metric_events"] = [s.spec.event for s in self._slots]
        params["conversion_events"] = [s.spec.event for s in self._charted_slots]
        for slot in self._slots:
            params[f"metric_{slot.index}_event"] = slot.spec.event
        return params

    def decode_conversion_rows(
        self, rows: Sequence[Sequence[Any]], column_names: Sequence[str]
    ) -> dict[int, list[ConversionBucket]]:
        """Group conversions-query rows by the metric behind each slot index.
        Every charted metric gets a key, empty when nobody converted yet."""
        index = {name: position for position, name in enumerate(column_names)}
        buckets: dict[int, list[ConversionBucket]] = {
            slot.spec.metric_id: [] for slot in self._charted_slots
        }
        for row in rows:
            metric_id = self._slots[int(row[index["metric_index"]])].spec.metric_id
            buckets[metric_id].append(
                ConversionBucket(
                    variant=str(row[index["variant"]]),
                    bucket=row[index["bucket"]],
                    converted_identities=int(row[index["converted_identities"]]),
                )
            )
        return buckets

    def decode_rows(
        self, rows: list[Any], column_names: Sequence[str]
    ) -> tuple[dict[str, int], dict[int, dict[str, VariantStats]]]:
        """Decode raw ClickHouse rows into exposure counts and per-metric stats.

        Columns are located by name, so a missing one raises KeyError rather than
        silently reading a neighbour's value.
        """
        index = {name: position for position, name in enumerate(column_names)}
        exposure_counts: dict[str, int] = {}
        metric_stats: dict[int, dict[str, VariantStats]] = {
            slot.spec.metric_id: {} for slot in self._slots
        }
        for row in rows:
            variant = str(row[index["variant"]])
            n = int(row[index["n"]])
            exposure_counts[variant] = n
            for slot in self._slots:
                metric_stats[slot.spec.metric_id][variant] = slot.decode(n, row, index)
        return exposure_counts, metric_stats
