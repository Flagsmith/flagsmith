from google.rpc import code_pb2
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace import status as status_module


class QueryLogger:
    def __init__(self):
        self.queries = []

    def _get_current_tracer(self):
        """Get the current request tracer."""
        return execution_context.get_opencensus_tracer()

    def __call__(self, execute, sql, params, many, context):
        tracer = self._get_current_tracer()
        if not tracer:
            return execute(sql, params, many, context)

        vendor = context["connection"].vendor
        alias = context["connection"].alias

        span = tracer.start_span()
        span.name = "{}.query".format(vendor)
        span.span_kind = span_module.SpanKind.CLIENT

        tracer.add_attribute_to_current_span("component", vendor)
        tracer.add_attribute_to_current_span("db.instance", alias)
        tracer.add_attribute_to_current_span("db.statement", sql)
        tracer.add_attribute_to_current_span("db.type", "sql")

        try:
            result = execute(sql, params, many, context)
        except Exception as e:  # pragma: NO COVER
            status = status_module.Status(
                code=code_pb2.UNKNOWN, message=f"DB error ({e.__class__.__name__}): {e}"
            )
            span.set_status(status)
            raise
        else:
            return result
        finally:
            tracer.end_span()
