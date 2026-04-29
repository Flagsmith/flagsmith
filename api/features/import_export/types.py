from typing import TypedDict


class FeatureExportMultivariateData(TypedDict):
    percentage_allocation: float
    default_percentage_allocation: float
    value: str | int | bool | None
    type: str


class FeatureExportData(TypedDict):
    name: str
    default_enabled: bool
    is_server_key_only: bool
    initial_value: str | None
    value: str | int | bool | None
    type: str
    enabled: bool
    multivariate: list[FeatureExportMultivariateData]
