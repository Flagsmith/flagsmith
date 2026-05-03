"""Constants for the segment membership index."""

from typing import Literal

# Atom kinds — partition by the property class. Set by
# `map_segment_condition_to_atom_kind` in `mappers.py`.
AtomKind = Literal["trait", "identifier", "identity_key", "environment_name"]

KIND_TRAIT: AtomKind = "trait"
KIND_IDENTIFIER: AtomKind = "identifier"
KIND_IDENTITY_KEY: AtomKind = "identity_key"
KIND_ENVIRONMENT_NAME: AtomKind = "environment_name"

# JSONPath properties recognised by the engine for non-trait context values.
PROPERTY_IDENTITY_IDENTIFIER = "$.identity.identifier"
PROPERTY_IDENTITY_KEY = "$.identity.key"
PROPERTY_ENVIRONMENT_NAME = "$.environment.name"
