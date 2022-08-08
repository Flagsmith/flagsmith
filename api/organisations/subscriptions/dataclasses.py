from dataclasses import dataclass


@dataclass
class BaseSubscriptionMetadata:
    seats: int = 0
    api_calls: int = 0
    projects: int = 0

    payment_source: str = None

    def __add__(self, other):
        return BaseSubscriptionMetadata(
            seats=self.seats + other.seats,
            api_calls=self.api_calls + other.api_calls,
            projects=self.projects + other.projects,
        )
