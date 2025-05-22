import typing
from datetime import datetime

from django.utils import timezone
from features.versioning.constants import DEFAULT_VERSION_LIMIT_DAYS


class BaseSubscriptionMetadata:
    payment_source = None

    def __init__(  # type: ignore[no-untyped-def]
        self,
        seats: int = 0,
        api_calls: int = 0,
        projects: None | int = None,
        chargebee_email: None | str = None,
        audit_log_visibility_days: int | None = 0,
        feature_history_visibility_days: int | None = DEFAULT_VERSION_LIMIT_DAYS,
        **kwargs,  # allows for extra unknown attrs from CB json metadata
    ) -> None:
        self.seats = seats
        self.api_calls = api_calls
        self.projects = projects
        self.chargebee_email = chargebee_email
        self.audit_log_visibility_days = audit_log_visibility_days
        self.feature_history_visibility_days = feature_history_visibility_days

    def __add__(self, other: "BaseSubscriptionMetadata"):  # type: ignore[no-untyped-def]
        if self.payment_source != other.payment_source:
            raise TypeError(
                "Cannot add SubscriptionMetadata from multiple payment sources."
            )

        return self.__class__(
            seats=self.seats + other.seats,
            api_calls=self.api_calls + other.api_calls,
            projects=_add_nullable_limit_attributes(self.projects, other.projects),
            chargebee_email=self.chargebee_email,
            audit_log_visibility_days=_add_nullable_limit_attributes(
                self.audit_log_visibility_days,
                other.audit_log_visibility_days,
                addition_function=max,
            ),
            feature_history_visibility_days=_add_nullable_limit_attributes(
                self.feature_history_visibility_days,
                other.feature_history_visibility_days,
                addition_function=max,
            ),
        )

    def __str__(self):  # type: ignore[no-untyped-def]
        return (
            "%s Subscription Metadata (seats: %d, api_calls: %d, projects: %s, "
            "chargebee_email: %s, audit_log_visibility_days: %s, feature_history_visibility_days: %s)"
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
                self.audit_log_visibility_days,
                self.feature_history_visibility_days,
            )
        )

    def __repr__(self):  # type: ignore[no-untyped-def]
        return str(self)

    def __eq__(self, other: "BaseSubscriptionMetadata"):  # type: ignore[override,no-untyped-def]
        return (
            self.seats == other.seats
            and self.api_calls == other.api_calls
            and self.projects == other.projects
            and self.payment_source == other.payment_source
            and self.chargebee_email == other.chargebee_email
            and self.audit_log_visibility_days == other.audit_log_visibility_days
            and self.feature_history_visibility_days
            == other.feature_history_visibility_days
        )


def _add_nullable_limit_attributes(
    first: int | None,
    second: int | None,
    addition_function: typing.Callable[[typing.Tuple[int, int]], int] = sum,
) -> int | None:
    """
    Add 2 nullable attributes where None implies no limit (and hence is the maximum
    value). Based on this, if either attribute is None, we return None.
    """
    if first is None or second is None:
        return None
    return addition_function((first, second))
