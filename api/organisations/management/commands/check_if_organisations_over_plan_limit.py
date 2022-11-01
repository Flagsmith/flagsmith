from django.core.management import BaseCommand

from organisations.models import Organisation
from organisations.tasks import send_org_over_limit_alert


class Command(BaseCommand):
    def handle(self, *args, **options):
        for org in Organisation.objects.all():
            if org.over_plan_seats_limit() and not org.alerted_over_plan_limit:
                send_org_over_limit_alert.delay(args=(org.id,))
                org.alerted_over_plan_limit = True
                org.save()
