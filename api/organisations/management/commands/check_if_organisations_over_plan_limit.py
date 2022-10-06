from django.core.management import BaseCommand

from organisations.models import Organisation
from organisations.subscriptions.subscription_service import (
    get_subscription_metadata,
)
from users.models import FFAdminUser


class Command(BaseCommand):
    def handle(self, *args, **options):
        for org in Organisation.objects.all():
            if org.over_plan_seats_limit() and not org.alerted_over_plan_limit:
                send_alert(org)
                org.alerted_over_plan_limit = True
                org.save()


def send_alert(organisation):
    subscription_metadata = get_subscription_metadata(organisation)
    FFAdminUser.send_alert_to_admin_users(
        subject="Organisation over number of seats",
        message="Organisation %s has used %d seats which is over their plan limit of %d "
        "(plan: %s)"
        % (
            str(organisation.name),
            organisation.num_seats,
            subscription_metadata.seats,
            organisation.subscription.plan,
        ),
    )
