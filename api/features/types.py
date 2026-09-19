from typing_extensions import NotRequired, TypedDict


class FeatureEngineMetadata(TypedDict):
    """Core API data carried on a `FeatureContext` and returned on a `FlagResult`.

    The engine treats this as opaque. It exists so that callers can map an
    evaluated flag back to the Django rows it was built from, without
    re-deriving which override won.
    """

    feature_id: int
    feature_state_id: int
    #: Set when the context was built from a segment override.
    segment_id: NotRequired[int]
    #: Set when the context was built from an identity override.
    identity_id: NotRequired[int]
