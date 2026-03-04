from typing import Any

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import BooleanField, Func
from django.db.models.sql.compiler import SQLCompiler


class ArrayContains(Func):
    """Generates: array_col @> ARRAY[value]::text[]

    Used to check whether a text array column contains a single expression
    value, in a form that PostgreSQL can satisfy with a GIN index. The
    standard ArrayField __contains lookup only accepts concrete Python values,
    not ORM expressions such as F() or OuterRef(), hence this helper.
    """

    output_field = BooleanField()

    def as_sql(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        *_: Any,
        **extra_context: Any,
    ) -> tuple[str, list[str | int] | tuple[str | int, ...] | tuple[()]]:
        array_expr, value_expr = self.source_expressions
        array_sql, array_params = compiler.compile(array_expr)
        value_sql, value_params = compiler.compile(value_expr)
        return f"{array_sql} @> ARRAY[{value_sql}]::text[]", [
            *array_params,
            *value_params,
        ]
