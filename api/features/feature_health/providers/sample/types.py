import typing

SampleEventStatus: typing.TypeAlias = typing.Literal["healthy", "unhealthy"]


class SampleEvent(typing.TypedDict):
    environment: typing.NotRequired[str]
    feature: str
    status: SampleEventStatus
    reason: typing.NotRequired[str]
