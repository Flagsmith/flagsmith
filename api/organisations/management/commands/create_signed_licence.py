import argparse
import json
from typing import Any

from django.core.management import BaseCommand

from organisations.subscriptions.licensing.helpers import (
    PrivateKeyMissingError,
    sign_licence,
)


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--organisation-name",
            type=str,
            dest="organisation_name",
            help="Name of the organisation",
        )
        parser.add_argument(
            "--plan-id",
            type=str,
            dest="plan_id",
            help="Plan id for the organisation",
        )
        parser.add_argument(
            "--num-seats",
            type=int,
            dest="num_seats",
            help="Number of seats available to the organisation",
            default=1,
        )
        parser.add_argument(
            "--num-projects",
            type=int,
            dest="num_projects",
            help="Number of projects available to the organisation",
            default=1,
        )
        parser.add_argument(
            "--num-api-calls",
            type=int,
            dest="num_api_calls",
            help="Number of API calls available to the organisation",
            default=1_000_000,
        )

    def handle(
        self,
        *args: Any,
        organisation_name: str,
        plan_id: str,
        num_seats: int,
        num_projects: int,
        num_api_calls: int,
        **options: Any,
    ) -> None:
        self.stdout.write(
            self.style.NOTICE(
                "Don't forget to increment the project count by 1 to "
                "account for Flagsmith on Flagsmith projects."
            )
        )
        licence_content = {
            "organisation_name": organisation_name,
            "plan_id": plan_id,
            "num_seats": num_seats,
            "num_projects": num_projects,
            "num_api_calls": num_api_calls,
        }

        licence = json.dumps(licence_content)

        try:
            licence_signature = sign_licence(licence)
        except PrivateKeyMissingError:
            self.stdout.write(
                self.style.NOTICE(
                    "Missing settings.SUBSCRIPTION_LICENCE_PRIVATE_KEY to sign licence. It can be found in Bitwarden."
                )
            )

        self.stdout.write(self.style.SUCCESS("Here is the licence:"))
        self.stdout.write(licence)
        self.stdout.write(self.style.SUCCESS("Here is the signature:"))
        self.stdout.write(licence_signature)
