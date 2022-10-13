from organisations.subscriptions.subscription_service import (
    get_subscription_metadata,
)
from users.models import FFAdminUser

ALERT_EMAIL_MESSAGE = (
    "Organisation %s has used %d seats which is over their plan limit of %d (plan: %s)"
)
ALERT_EMAIL_SUBJECT = "Organisation over number of seats"


def send_org_over_limit_alert(organisation):
    subscription_metadata = get_subscription_metadata(organisation)
    FFAdminUser.send_alert_to_admin_users(
        subject=ALERT_EMAIL_SUBJECT,
        message=ALERT_EMAIL_MESSAGE
        % (
            str(organisation.name),
            organisation.num_seats,
            subscription_metadata.seats,
            organisation.subscription.plan
            if subscription_metadata.payment_source
            else "Free",
        ),
    )
