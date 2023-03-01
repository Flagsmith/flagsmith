import typing
from dataclasses import dataclass


@dataclass
class EnvironmentFeatureOverridesData:
    """
    Dataclass to hold the information about the number of overrides for a given feature in a given
    environment.
    """

    num_segment_overrides: int = 0
    num_identity_overrides: typing.Optional[int] = None

    def add_identity_override(self):
        if self.num_identity_overrides is None:
            self.num_identity_overrides = 1
        else:
            self.num_identity_overrides += 1
