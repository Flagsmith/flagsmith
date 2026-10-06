from collections.abc import Mapping, Sequence
from typing import Protocol

from experimentation.types import ExposureGranularity


class Dialect(Protocol):
    """The SQL fragments that differ between warehouses. A warehouse needing a
    differently shaped query overrides that query in its provider instead."""

    def param(self, name: str) -> str: ...

    def in_list(self, expr: str, name: str, size: int) -> str: ...

    def list_params(self, name: str, values: Sequence[str]) -> dict[str, object]: ...

    def count_all(self) -> str: ...

    def count_if(self, cond: str) -> str: ...

    def count_distinct(self, expr: str) -> str: ...

    def any_value(self, expr: str) -> str: ...

    def time_bucket(self, expr: str, granularity: ExposureGranularity) -> str: ...

    def float_or_zero(self, expr: str) -> str: ...

    def sum_if(self, expr: str, cond: str) -> str:
        """Zero, not NULL, when no row matches."""
        ...

    def avg_if(self, expr: str, cond: str) -> str:
        """Zero, not NULL, when no row matches."""
        ...

    def min_if(self, expr: str, cond: str) -> str:
        """NULL when no row matches."""
        ...

    def bool_to_number(self, expr: str) -> str: ...

    def zip_unnest(self, arrays: Mapping[str, Sequence[str]]) -> str:
        """One row per array position, each array's element in the column its key names."""
        ...


_CLICKHOUSE_BUCKET_FUNCTIONS: dict[ExposureGranularity, str] = {
    "hour": "toStartOfHour",
    "day": "toStartOfDay",
}


class ClickHouseDialect:
    def param(self, name: str) -> str:
        return f"%({name})s"

    def in_list(self, expr: str, name: str, size: int) -> str:
        return f"{expr} IN {self.param(name)}"

    def list_params(self, name: str, values: Sequence[str]) -> dict[str, object]:
        return {name: list(values)}

    def count_all(self) -> str:
        return "count()"

    def count_if(self, cond: str) -> str:
        return f"countIf({cond})"

    def count_distinct(self, expr: str) -> str:
        return f"uniqExact({expr})"

    def any_value(self, expr: str) -> str:
        return f"any({expr})"

    def time_bucket(self, expr: str, granularity: ExposureGranularity) -> str:
        return f"{_CLICKHOUSE_BUCKET_FUNCTIONS[granularity]}({expr}, 'UTC')"

    def float_or_zero(self, expr: str) -> str:
        return f"toFloat64OrZero({expr})"

    def sum_if(self, expr: str, cond: str) -> str:
        return f"sumIf({expr}, {cond})"

    def avg_if(self, expr: str, cond: str) -> str:
        return f"if({self.count_if(cond)} > 0, avgIf({expr}, {cond}), 0)"

    def min_if(self, expr: str, cond: str) -> str:
        return f"minIfOrNull({expr}, {cond})"

    def bool_to_number(self, expr: str) -> str:
        return expr

    def zip_unnest(self, arrays: Mapping[str, Sequence[str]]) -> str:
        return "ARRAY JOIN " + ", ".join(
            f"[{', '.join(values)}] AS {alias}" for alias, values in arrays.items()
        )


CLICKHOUSE_DIALECT = ClickHouseDialect()
