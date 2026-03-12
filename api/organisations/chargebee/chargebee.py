import logging
from contextlib import suppress
from datetime import datetime
from typing import Any

from chargebee.api_error import (  # type: ignore[import-untyped]
    APIError as ChargebeeAPIError,
)
from chargebee.models.hosted_page.operations import (  # type: ignore[import-untyped]
    HostedPage as ChargebeeHostedPageOps,
)
from chargebee.models.hosted_page.responses import (  # type: ignore[import-untyped]
    HostedPageResponse,
)
from chargebee.models.plan.responses import (  # type: ignore[import-untyped]
    RetrieveResponse as ChargebeePlanRetrieveResponse,
)
from chargebee.models.portal_session.operations import (  # type: ignore[import-untyped]
    PortalSession as PortalSessionOps,
)
from chargebee.models.subscription.operations import (  # type: ignore[import-untyped]
    Subscription as SubscriptionOps,
)
from chargebee.models.subscription.responses import (  # type: ignore[import-untyped]
    SubscriptionResponse,
)
from pytz import UTC

from organisations.chargebee.cache import ChargebeeCache
from organisations.chargebee.client import chargebee_client
from organisations.chargebee.constants import (
    ADDITIONAL_API_SCALE_UP_ADDON_ID,
    ADDITIONAL_API_START_UP_ADDON_ID,
    ADDITIONAL_SEAT_ADDON_ID,
)
from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.exceptions import (
    CannotCancelChargebeeSubscription,
    UpgradeAPIUsageError,
    UpgradeAPIUsagePaymentFailure,
    UpgradeSeatsError,
    UpgradeSeatsPaymentFailure,
)

logger = logging.getLogger(__name__)

CHARGEBEE_PAYMENT_ERROR_CODES = [
    "payment_processing_failed",
    "payment_method_verification_failed",
    "payment_method_not_present",
    "payment_gateway_currency_incompatible",
    "payment_intent_invalid",
    "payment_intent_invalid_amount",
]


def get_subscription_data_from_hosted_page(
    hosted_page_id: str,
) -> dict[str, Any]:
    hosted_page = get_hosted_page(hosted_page_id)
    subscription = get_subscription_from_hosted_page(hosted_page)
    if not subscription:
        return {}
    plan_metadata = get_plan_meta_data(subscription["plan_id"])
    return {
        "subscription_id": subscription["id"],
        "plan": subscription["plan_id"],
        "subscription_date": datetime.fromtimestamp(subscription["created_at"], tz=UTC),
        "max_seats": get_max_seats_for_plan(plan_metadata),
        "max_api_calls": get_max_api_calls_for_plan(plan_metadata),
        "customer_id": get_customer_id_from_hosted_page(hosted_page),
        "payment_method": CHARGEBEE,
    }


def get_hosted_page(hosted_page_id: str) -> HostedPageResponse:
    response = chargebee_client.HostedPage.retrieve(hosted_page_id)
    return response.hosted_page


def get_subscription_from_hosted_page(
    hosted_page: HostedPageResponse,
) -> dict[str, Any] | None:
    content = hosted_page.content
    if content and "subscription" in content:
        return content["subscription"]  # type: ignore[no-any-return]
    return None


def get_customer_id_from_hosted_page(
    hosted_page: HostedPageResponse,
) -> str | None:
    content = hosted_page.content
    if content and "customer" in content:
        return content["customer"]["id"]  # type: ignore[no-any-return]
    return None


def get_max_seats_for_plan(meta_data: dict[str, Any]) -> int:
    return int(meta_data.get("seats", 1))


def get_max_api_calls_for_plan(meta_data: dict[str, Any]) -> int:
    return int(meta_data.get("api_calls", 50000))


def get_plan_meta_data(plan_id: str) -> dict[str, Any]:
    plan_details = get_plan_details(plan_id)
    if plan_details and hasattr(plan_details.plan, "meta_data"):
        return plan_details.plan.meta_data or {}
    return {}


def get_plan_details(plan_id: str) -> ChargebeePlanRetrieveResponse | None:
    if plan_id:
        return chargebee_client.Plan.retrieve(plan_id)
    return None


def get_portal_url(customer_id: str, redirect_url: str) -> str | None:
    result = chargebee_client.PortalSession.create(
        PortalSessionOps.CreateParams(
            redirect_url=redirect_url,
            customer=PortalSessionOps.CreateCustomerParams(
                id=customer_id,
            ),
        )
    )
    if result and hasattr(result, "portal_session"):
        return result.portal_session.access_url  # type: ignore[no-any-return]
    return None


def get_customer_id_from_subscription_id(subscription_id: str) -> str | None:
    subscription_response = chargebee_client.Subscription.retrieve(subscription_id)
    if hasattr(subscription_response, "customer"):
        return subscription_response.customer.id  # type: ignore[no-any-return]
    return None


def get_hosted_page_url_for_subscription_upgrade(
    subscription_id: str, plan_id: str
) -> str:
    checkout_existing_response = chargebee_client.HostedPage.checkout_existing(
        ChargebeeHostedPageOps.CheckoutExistingParams(
            subscription=ChargebeeHostedPageOps.CheckoutExistingSubscriptionParams(
                id=subscription_id,
                plan_id=plan_id,
            ),
        )
    )
    return checkout_existing_response.hosted_page.url  # type: ignore[no-any-return]


def extract_subscription_metadata(
    chargebee_subscription: dict[str, Any],
    customer_email: str,
) -> ChargebeeObjMetadata:
    chargebee_addons = chargebee_subscription.get("addons", [])
    chargebee_cache = ChargebeeCache()  # type: ignore[no-untyped-call]
    subscription_metadata: ChargebeeObjMetadata = chargebee_cache.plans[
        chargebee_subscription["plan_id"]
    ]
    subscription_metadata.chargebee_email = customer_email

    for addon in chargebee_addons:
        quantity = addon.get("quantity") or 1
        addon_metadata: ChargebeeObjMetadata = (
            chargebee_cache.addons[addon["id"]] * quantity
        )
        subscription_metadata = subscription_metadata + addon_metadata

    return subscription_metadata


def get_subscription_metadata_from_id(
    subscription_id: str,
) -> ChargebeeObjMetadata | None:
    if not (subscription_id and subscription_id.strip() != ""):
        logger.warning("Subscription id is empty or None")
        return None

    with suppress(ChargebeeAPIError):
        chargebee_result = chargebee_client.Subscription.retrieve(subscription_id)
        chargebee_subscription = _convert_chargebee_subscription_to_dictionary(
            chargebee_result.subscription
        )

        return extract_subscription_metadata(
            chargebee_subscription,
            chargebee_result.customer.email,
        )

    return None


def cancel_subscription(subscription_id: str) -> None:
    try:
        chargebee_client.Subscription.cancel(
            subscription_id,
            SubscriptionOps.CancelParams(end_of_term=True),
        )
    except ChargebeeAPIError as e:
        msg = "Cannot cancel CB subscription for subscription id: %s" % subscription_id
        logger.error(msg)
        raise CannotCancelChargebeeSubscription(msg) from e


def add_single_seat(subscription_id: str) -> None:
    try:
        subscription = chargebee_client.Subscription.retrieve(
            subscription_id
        ).subscription
        addons = subscription.addons or []
        current_seats = next(
            (
                addon.quantity
                for addon in addons
                if addon.id == ADDITIONAL_SEAT_ADDON_ID
            ),
            0,
        )

        chargebee_client.Subscription.update(
            subscription_id,
            SubscriptionOps.UpdateParams(
                addons=[
                    SubscriptionOps.UpdateAddonParams(
                        id=ADDITIONAL_SEAT_ADDON_ID,
                        quantity=current_seats + 1,
                    )
                ],
                prorate=True,
                invoice_immediately=False,
            ),
        )

    except ChargebeeAPIError as e:
        api_error_code = e.json_obj["api_error_code"]
        if api_error_code in CHARGEBEE_PAYMENT_ERROR_CODES:
            logger.warning(
                f"Payment declined ({api_error_code}) during additional "
                f"seat upgrade to a CB subscription for subscription_id "
                f"{subscription_id}"
            )
            raise UpgradeSeatsPaymentFailure() from e

        msg = (
            "Failed to add additional seat to CB subscription for subscription id: %s"
            % subscription_id
        )
        logger.error(msg)
        raise UpgradeSeatsError(msg) from e


def add_100k_api_calls_start_up(
    subscription_id: str, count: int = 1, invoice_immediately: bool = False
) -> None:
    add_100k_api_calls(ADDITIONAL_API_START_UP_ADDON_ID, subscription_id, count)


def add_100k_api_calls_scale_up(
    subscription_id: str, count: int = 1, invoice_immediately: bool = False
) -> None:
    add_100k_api_calls(ADDITIONAL_API_SCALE_UP_ADDON_ID, subscription_id, count)


def add_100k_api_calls(
    addon_id: str,
    subscription_id: str,
    count: int = 1,
    invoice_immediately: bool = False,
) -> None:
    if not count:
        return
    try:
        chargebee_client.Subscription.update(
            subscription_id,
            SubscriptionOps.UpdateParams(
                addons=[
                    SubscriptionOps.UpdateAddonParams(
                        id=addon_id,
                        quantity=count,
                    )
                ],
                prorate=False,
                invoice_immediately=invoice_immediately,
            ),
        )

    except ChargebeeAPIError as e:
        api_error_code = e.json_obj["api_error_code"]
        if api_error_code in CHARGEBEE_PAYMENT_ERROR_CODES:
            logger.warning(
                f"Payment declined ({api_error_code}) during additional "
                f"api calls upgrade to a CB subscription for subscription_id "
                f"{subscription_id}"
            )
            raise UpgradeAPIUsagePaymentFailure() from e

        msg = (
            "Failed to add additional API calls to CB subscription for subscription id: %s"
            % subscription_id
        )
        logger.error(msg)
        raise UpgradeAPIUsageError(msg) from e


def _convert_chargebee_subscription_to_dictionary(
    chargebee_subscription: SubscriptionResponse,
) -> dict[str, Any]:
    chargebee_subscription_dict = dict(chargebee_subscription.raw_data)
    addons = chargebee_subscription.addons or []
    chargebee_subscription_dict["addons"] = [dict(addon.raw_data) for addon in addons]

    return chargebee_subscription_dict
