from django.conf import settings
from django.core.mail import send_mail
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
    send_mail(
        subject='Organisation over number of seats',
        message='Organisation %s has gone over the limit on '
                'number of seats (plan: %s)' % (str(organisation.name), organisation.subscription.plan),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=FFAdminUser.get_admin_user_emails(),
        fail_silently=True
    )
