from typing import Literal

FeatureType = Literal["STANDARD", "MULTIVARIATE"]

MULTIVARIATE: FeatureType = "MULTIVARIATE"
STANDARD: FeatureType = "STANDARD"

# the following two types have been merged in terms of functionality
# but kept for now until the FE is updated
CONFIG = "CONFIG"
FLAG = "FLAG"
