import logging
from datetime import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from organisations.chargebee.tasks import update_chargebee_cache
from organisations.models import (
    OrganisationSubscriptionInformationCache,
    Subscription,
)
from organisations.subscriptions.constants import (
    SUBSCRIPTION_BILLING_STATUS_ACTIVE,
    SUBSCRIPTION_BILLING_STATUS_DUNNING,
)

from .chargebee import extract_subscription_metadata
from .serializers import (
    PaymentFailedSerializer,
    PaymentSucceededSerializer,
    ProcessSubscriptionSerializer,
)

logger = logging.getLogger(__name__)


def cache_rebuild_event(request: Request) -> Response:
    logger.info("Chargebee plan or addon webhook fired, rebuilding cache.")
    update_chargebee_cache.delay()
    return Response(status=status.HTTP_200_OK)


def payment_failed(request: Request) -> Response:
    serializer = PaymentFailedSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError:
        logger.warning(
            "Serializer failure during chargebee payment failed processing",
            exc_info=True,
        )
        return Response(status=status.HTTP_200_OK)

    subscription_id = serializer.validated_data["content"]["invoice"]["subscription_id"]

    try:
        subscription = Subscription.objects.get(subscription_id=subscription_id)
    except Subscription.DoesNotExist:
        logger.warning(
            "No matching subscription for chargebee payment "
            f"failed webhook for subscription id {subscription_id}"
        )
        return Response(status=status.HTTP_200_OK)
    except Subscription.MultipleObjectsReturned:
        logger.warning(
            "Multiple matching subscriptions for chargebee payment "
            f"failed webhook for subscription id {subscription_id}"
        )
        return Response(status=status.HTTP_200_OK)

    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_DUNNING
    subscription.save()

    return Response(status=status.HTTP_200_OK)


def payment_succeeded(request: Request) -> Response:
    serializer = PaymentSucceededSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError:
        logger.warning(
            "Serializer failure during chargebee payment failed processing",
            exc_info=True,
        )
        return Response(status=status.HTTP_200_OK)

    subscription_id = serializer.validated_data["content"]["invoice"]["subscription_id"]

    try:
        subscription = Subscription.objects.get(subscription_id=subscription_id)
    except Subscription.DoesNotExist:
        logger.warning(
            "No matching subscription for chargebee payment "
            f"succeeded webhook for subscription id {subscription_id}"
        )
        return Response(status=status.HTTP_200_OK)
    except Subscription.MultipleObjectsReturned:
        logger.warning(
            "Multiple matching subscriptions for chargebee payment "
            f"succeeded webhook for subscription id {subscription_id}"
        )
        return Response(status=status.HTTP_200_OK)

    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_ACTIVE
    subscription.save()

    return Response(status=status.HTTP_200_OK)


def process_subscription(request: Request) -> Response:  # noqa: C901
    serializer = ProcessSubscriptionSerializer(data=request.data)

    # Since this function is a catchall, we're not surprised if
    # other webhook events fail to process.
    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError:
        return Response(status=status.HTTP_200_OK)

    subscription = serializer.validated_data["content"]["subscription"]
    customer = serializer.validated_data["content"]["customer"]
    try:
        existing_subscription = Subscription.objects.get(
            subscription_id=subscription["id"]
        )
    except (Subscription.DoesNotExist, Subscription.MultipleObjectsReturned):
        logger.warning(
            f"Couldn't get unique subscription for ChargeBee id {subscription['id']}"
        )
        return Response(status=status.HTTP_200_OK)

    if subscription["status"] in ("non_renewing", "cancelled"):
        existing_subscription.prepare_for_cancel(
            datetime.fromtimestamp(subscription.get("current_term_end")).replace(
                tzinfo=timezone.utc
            ),
            update_chargebee=False,
        )
        return Response(status=status.HTTP_200_OK)

    if subscription["status"] != "active":
        # Nothing to do, so return early.
        return Response(status=status.HTTP_200_OK)

    if subscription["plan_id"] != existing_subscription.plan:
        existing_subscription.update_plan(subscription["plan_id"])

    subscription_metadata = extract_subscription_metadata(
        chargebee_subscription=subscription,
        customer_email=customer["email"],
    )
    osic_defaults = {
        "chargebee_updated_at": timezone.now(),
        "allowed_30d_api_calls": subscription_metadata.api_calls,
        "allowed_seats": subscription_metadata.seats,
        "organisation_id": existing_subscription.organisation_id,
        "allowed_projects": subscription_metadata.projects,
        "chargebee_email": subscription_metadata.chargebee_email,
    }

    if "current_term_end" in subscription:
        current_term_end = subscription["current_term_end"]
        if current_term_end is None:
            osic_defaults["current_billing_term_ends_at"] = None
        else:
            osic_defaults["current_billing_term_ends_at"] = datetime.fromtimestamp(
                current_term_end
            ).replace(tzinfo=timezone.utc)

    if "current_term_start" in subscription:
        current_term_start = subscription["current_term_start"]
        if current_term_start is None:
            osic_defaults["current_billing_term_starts_at"] = None
        else:
            osic_defaults["current_billing_term_starts_at"] = datetime.fromtimestamp(
                current_term_start
            ).replace(tzinfo=timezone.utc)

    OrganisationSubscriptionInformationCache.objects.update_or_create(
        organisation_id=existing_subscription.organisation_id,
        defaults=osic_defaults,
    )
    return Response(status=status.HTTP_200_OK)
