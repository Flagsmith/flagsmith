from typing import TYPE_CHECKING

from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
    from flagsmith_schemas.dynamodb import FeatureState as EdgeFeatureState

    from features.models import FeatureState


class FeatureEngineMetadata(TypedDict):
    """Core API data carried on a `FeatureContext` and back on a `FlagResult`.

    The engine treats this as opaque, so the feature state an evaluated flag
    came from can simply ride along, saving callers from working out which
    override won. Exactly one of the two is set, naming where it was read
    from.

    The annotations are deliberately forward references: nothing here may
    import Django at runtime, or `features.models` could not annotate against
    it.
    """

    feature_state: NotRequired["FeatureState"]
    #: An edge identity's own overrides are stored in DynamoDB rather than the
    #: ORM, so they reach evaluation as the model they were read back as.
    edge_feature_state: NotRequired["EdgeFeatureState"]
