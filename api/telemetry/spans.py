from opentelemetry import trace
from opentelemetry.util.types import AttributeValue


def set_span_attribute(attribute: str, value: AttributeValue) -> None:
    trace.get_current_span().set_attribute(attribute, value)


def get_span_attribute(attribute: str) -> AttributeValue | None:
    attributes = getattr(trace.get_current_span(), "attributes", None) or {}
    return attributes.get(attribute)
