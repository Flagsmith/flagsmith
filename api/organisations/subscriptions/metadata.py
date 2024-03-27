import typing


class BaseSubscriptionMetadata:
    payment_source = None

    def __init__(
        self,
        seats: int = 0,
        api_calls: int = 0,
        projects: typing.Optional[int] = None,
        chargebee_email=None,
    ):
        self.seats = seats
        self.api_calls = api_calls
        self.projects = projects
        self.chargebee_email = chargebee_email

    def __add__(self, other: "BaseSubscriptionMetadata"):
        if self.payment_source != other.payment_source:
            raise TypeError(
                "Cannot add SubscriptionMetadata from multiple payment sources."
            )

        if self.projects is not None and other.projects is not None:
            projects = self.projects + other.projects
        elif self.projects is None and other.projects is not None:
            projects = other.projects
        elif other.projects is None and self.projects is not None:
            projects = self.projects
        else:
            projects = None

        return self.__class__(
            seats=self.seats + other.seats,
            api_calls=self.api_calls + other.api_calls,
            projects=projects,
            chargebee_email=self.chargebee_email,
        )

    def __str__(self):
        return (
            "%s Subscription Metadata (seats: %d, api_calls: %d, projects: %s, chargebee_email: %s)"
            % (
                (
                    self.payment_source.title()
                    if self.payment_source is not None
                    else "unknown payment source"
                ),
                self.seats,
                self.api_calls,
                str(self.projects) if self.projects is not None else "no limit",
                self.chargebee_email,
            )
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, other: "BaseSubscriptionMetadata"):
        return (
            self.seats == other.seats
            and self.api_calls == other.api_calls
            and self.projects == other.projects
            and self.payment_source == other.payment_source
            and self.chargebee_email == other.chargebee_email
        )
