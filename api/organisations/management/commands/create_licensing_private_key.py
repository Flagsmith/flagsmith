from typing import Any

from django.core.management import BaseCommand

from organisations.subscriptions.licensing.helpers import create_private_key


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(create_private_key())
