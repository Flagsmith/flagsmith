from django.core.management import BaseCommand

from integrations.flagsmith.flagsmith_service import update_environment_json


class Command(BaseCommand):
    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        update_environment_json()
