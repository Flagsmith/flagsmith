from typing import Any

from django.core.management import BaseCommand

from organisations.subscriptions.licensing.helpers import create_public_key


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        print(create_public_key())
