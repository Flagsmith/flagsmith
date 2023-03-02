import typing
from dataclasses import dataclass


@dataclass
class EnvironmentFeatureOverridesData:
    """
    Dataclass to hold the information about the number of overrides for a given feature in a given
    environment.

    Note that num_identity_overrides can be None to represent that the environment in question
    is edge enabled (and hence we can't currently determine how many identity overrides there are).
    """

    num_segment_overrides: int = 0
    num_identity_overrides: typing.Optional[int] = None

    def add_identity_override(self):
        """
        Add an identity override to the dataclass.

        This special method is here to simplify null checking logic.
        """
        if self.num_identity_overrides is None:
            self.num_identity_overrides = 1
        else:
            self.num_identity_overrides += 1
