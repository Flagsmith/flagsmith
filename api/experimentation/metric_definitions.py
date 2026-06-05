"""Versioned schemas for ``Metric.definition``.

``definition`` is a schema-less JSON column whose shape is versioned so it can
evolve without breaking stored rows. Each supported version has a validator
here; the client sends the version it built the definition with. To introduce a
new shape, add an entry to ``METRIC_DEFINITION_VALIDATORS``.
"""

from collections.abc import Callable

DefinitionValidator = Callable[[dict[str, object]], "str | None"]


def _validate_v1(definition: dict[str, object]) -> str | None:
    event = definition.get("event")
    if not event or not isinstance(event, str):
        return "Definition must specify a non-empty 'event'."
    return None


METRIC_DEFINITION_VALIDATORS: dict[int, DefinitionValidator] = {
    1: _validate_v1,
}


def validate_metric_definition(definition: object) -> str | None:
    """Return an error message if ``definition`` is invalid, else ``None``."""
    if not isinstance(definition, dict):
        return "Definition must be an object."

    version = definition.get("version")
    validator = (
        METRIC_DEFINITION_VALIDATORS.get(version) if isinstance(version, int) else None
    )
    if validator is None:
        return "Definition must specify a supported 'version'."

    return validator(definition)
