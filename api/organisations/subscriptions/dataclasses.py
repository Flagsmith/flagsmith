import typing


class BaseSubscriptionMetadata:
    def __init__(
        self,
        seats: int = 0,
        api_calls: int = 0,
        projects: typing.Optional[int] = None,
        payment_source: str = None,
    ):
        self.seats = seats
        self.api_calls = api_calls
        self.projects = projects
        self.payment_source = payment_source

    def __add__(self, other: "BaseSubscriptionMetadata"):
        if self.payment_source != other.payment_source:
            raise TypeError(
                "Cannot add SubscriptionMetadata from multiple payment sources."
            )

        return BaseSubscriptionMetadata(
            seats=self.seats + other.seats,
            api_calls=self.api_calls + other.api_calls,
            projects=self.projects + other.projects,
            payment_source=self.payment_source,
        )

    def __str__(self):
        return "%s Subscription Metadata (seats: %d, api_calls: %d, projects: %s)" % (
            self.payment_source.title(),
            self.seats,
            self.api_calls,
            str(self.projects) if self.projects is not None else "no limit",
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, other: "BaseSubscriptionMetadata"):
        return (
            self.seats == other.seats
            and self.api_calls == other.api_calls
            and self.projects == other.projects
            and self.payment_source == other.payment_source
        )
