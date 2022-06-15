import typing

from django.views import View

from organisations.models import Subscription
from organisations.subscriptions.exceptions import InvalidSubscriptionPlanError


def require_plan(
    valid_plan_ids: typing.Iterable[str],
    view: View,
    subscription_retriever: typing.Callable[[View], Subscription],
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            sub = subscription_retriever(view)
            if sub.plan not in valid_plan_ids:
                raise InvalidSubscriptionPlanError(
                    f"Resource not available on plan {sub.plan}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
