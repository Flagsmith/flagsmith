from django.core.management import BaseCommand

from organisations.models import Organisation
from users.models import FFAdminUser


class Command(BaseCommand):
    def handle(self, *args, **options):
        for org in Organisation.objects.all():
            if org.over_plan_seats_limit() and not org.alerted_over_plan_limit:
                send_alert(org)
                org.alerted_over_plan_limit = True
                org.save()


def send_alert(organisation):
    FFAdminUser.send_alert_to_admin_users(
        subject="Organisation over number of seats",
        message="Organisation %s has used %d seats which is over their plan limit of %d "
        "(plan: %s)"
        % (
            str(organisation.name),
            organisation.num_seats,
            organisation.subscription.max_seats,
            organisation.subscription.plan,
        ),
    )
