import typing

from django.conf import settings
from rest_framework.request import Request

from organisations.models import Subscription
from organisations.subscriptions.exceptions import InvalidSubscriptionPlanError


def require_plan(
    valid_plan_ids: typing.Iterable[str],
    subscription_retriever: typing.Callable[[Request], Subscription],
):
    """
    Decorator to be used on view functions / methods that require a specific plan.

    Will result in 403 if resource requested is not part of an organisation that has
    the correct subscription.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not (args and isinstance(args[0], Request)):
                raise ValueError(
                    "require_plan decorator must be used on methods / functions whose "
                    "first argument is a Request object."
                )
            if settings.NO_SUBSCRIPTION_NEEDED:
                return func(*args, **kwargs)

            sub = subscription_retriever(args[0])
            if not sub or sub.plan not in valid_plan_ids:
                raise InvalidSubscriptionPlanError(
                    f"Resource not available on plan {sub.plan}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
