from datetime import datetime
from typing import TYPE_CHECKING

from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from features.models import FeatureState
    from features.multivariate.models import MultivariateFeatureOption
    from features.versioning.models import EnvironmentFeatureVersion
    from features.workflows.core.models import ChangeRequest
    from util.engine_models.features.models import FeatureStateModel


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
    edge_feature_state: NotRequired["FeatureStateModel"]


class LegacyFeatureStateValueData(TypedDict, total=False):
    """A feature state value, as validated by the legacy feature state APIs.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """

    type: str
    string_value: str | None
    integer_value: int | None
    boolean_value: bool | None


class LegacyMultivariateFeatureStateValueData(TypedDict):
    """A variant weight, as validated by the legacy feature state APIs.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """

    multivariate_feature_option: "MultivariateFeatureOption"
    percentage_allocation: float


class LegacyFeatureStateData(TypedDict, total=False):
    """A feature state, as validated by the legacy feature state APIs.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """

    enabled: bool
    feature_state_value: LegacyFeatureStateValueData
    multivariate_feature_state_values: list[LegacyMultivariateFeatureStateValueData]
    identity: "Identity | None"
    environment_feature_version: "EnvironmentFeatureVersion | None"
    change_request: "ChangeRequest | None"
    live_from: datetime | None
