from typing import get_args

from flagsmith_schemas.types import FeatureType

__all__ = (
    "FeatureType",
    "CONFIG",
    "FEATURE_TYPE_CHOICES",
    "FLAG",
    "MULTIVARIATE",
    "STANDARD",
)

MULTIVARIATE: FeatureType = "MULTIVARIATE"
STANDARD: FeatureType = "STANDARD"

FEATURE_TYPE_CHOICES = [(v, v) for v in get_args(FeatureType)]

# the following two types have been merged in terms of functionality
# but kept for now until the FE is updated
CONFIG = "CONFIG"
"""Deprecated."""
FLAG = "FLAG"
"""Deprecated."""
