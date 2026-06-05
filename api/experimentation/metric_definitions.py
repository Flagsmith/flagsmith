"""Versioned schemas for ``Metric.definition``.

``definition`` is a schema-less JSON column whose shape is versioned so it can
evolve without breaking stored rows. Each supported version has a validator
here; the client sends the version it built the definition with (sourced from
remote config on the frontend). To introduce a new shape, add an entry to
``METRIC_DEFINITION_VALIDATORS`` — the stats engine will key its SQL
construction on the same versions.
"""

from collections.abc import Callable

DefinitionValidator = Callable[[dict[str, object]], "str | None"]


def _validate_v1(definition: dict[str, object]) -> str | None:
    event = definition.get("event")
    if not event or not isinstance(event, str):
        return "Definition must specify a non-empty 'event'."
    return None


# Supported definition versions -> their validator. Add an entry per new shape.
METRIC_DEFINITION_VALIDATORS: dict[int, DefinitionValidator] = {
    1: _validate_v1,
}


def validate_metric_definition(definition: object) -> str | None:
    """Return an error message if ``definition`` is invalid, else ``None``."""
    if not isinstance(definition, dict):
        return "Definition must be an object."

    version = definition.get("version")
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version not in METRIC_DEFINITION_VALIDATORS
    ):
        supported = ", ".join(str(v) for v in sorted(METRIC_DEFINITION_VALIDATORS))
        return f"Definition must specify a supported 'version' ({supported})."

    return METRIC_DEFINITION_VALIDATORS[version](definition)
