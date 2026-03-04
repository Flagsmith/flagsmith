from django.db.models import BooleanField, Func


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
        compiler: object,
        connection: object,
        **extra_context: object,
    ) -> tuple[str, list[object]]:
        array_expr, value_expr = self.source_expressions
        array_sql, array_params = compiler.compile(array_expr)  # type: ignore[union-attr]
        value_sql, value_params = compiler.compile(value_expr)  # type: ignore[union-attr]
        return f"{array_sql} @> ARRAY[{value_sql}]::text[]", [
            *array_params,
            *value_params,
        ]
