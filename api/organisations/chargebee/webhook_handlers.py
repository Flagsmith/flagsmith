import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from organisations.models import Subscription
from organisations.subscriptions.constants import (
    SUBSCRIPTION_BILLING_STATUS_ACTIVE,
    SUBSCRIPTION_BILLING_STATUS_DUNNING,
)

from .serializers import PaymentFailedSerializer, PaymentSucceededSerializer

logger = logging.getLogger(__name__)


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
