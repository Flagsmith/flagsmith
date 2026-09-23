from typing import TYPE_CHECKING

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from features.models import FeatureState


class FeatureEngineMetadata(TypedDict):
    """Core API data carried on a `FeatureContext` and back on a `FlagResult`.

    The engine treats this as opaque, so the feature state an evaluated flag
    came from can simply ride along, saving callers from working out which
    override won.

    The annotations are deliberately forward references: nothing here may
    import Django at runtime, or `features.models` could not annotate against
    it.
    """

    feature_state: "FeatureState"
