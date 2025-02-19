import typing

from rest_framework.request import Request

from organisations.models import Subscription
from organisations.subscriptions.exceptions import InvalidSubscriptionPlanError


def require_plan(  # type: ignore[no-untyped-def]
    valid_plan_ids: typing.Iterable[str],
    subscription_retriever: typing.Callable[[Request], Subscription],
):
    """
    Decorator to be used on view functions / methods that require a specific plan.

    Will result in 403 if resource requested is not part of an organisation that has
    the correct subscription.
    """

    def decorator(func):  # type: ignore[no-untyped-def]
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            if not (args and isinstance(args[0], Request)):
                raise ValueError(
                    "require_plan decorator must be used on methods / functions whose "
                    "first argument is a Request object."
                )

            sub = subscription_retriever(args[0])
            if not sub or sub.plan not in valid_plan_ids:  # type: ignore[operator]
                raise InvalidSubscriptionPlanError(
                    f"Resource not available on plan {sub.plan}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
