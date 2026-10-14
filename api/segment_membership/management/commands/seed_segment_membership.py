"""Run an organisation's identity seed out of band.

The task processor is a poor host for an organisation large enough that the
seed outlives its task timeout: the run is marked failed while its thread keeps
going, retried alongside the thread that is still running, and re-enqueued
hourly once the retries are exhausted. Calling the task directly sidesteps all
of that, so the seed can be run as a standalone ECS task that no deployment
interrupts and nothing retries.

    flagsmith seed_segment_membership <organisation_id> [--ignore-feature-flag]

Base the ECS task definition on `flagsmith-task-processor`: it carries the
ClickHouse URL, the Dynamo table names, and the Flagsmith-on-Flagsmith server
key that the feature flag check needs.
"""

from argparse import ArgumentParser
from typing import Any

from django.core.management import BaseCommand

from segment_membership.tasks import seed_organisation_identities


class Command(BaseCommand):
    help = "Mirror an organisation's Dynamo identities into ClickHouse."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("organisation_id", type=int)
        parser.add_argument(
            "--ignore-feature-flag",
            action="store_true",
            help=(
                "Seed even though segment_membership_inspection is off for the "
                "organisation, so ClickHouse can be populated before the "
                "feature is exposed to it."
            ),
        )

    def handle(
        self,
        *args: Any,
        organisation_id: int,
        ignore_feature_flag: bool,
        **options: Any,
    ) -> None:
        seed_organisation_identities(
            organisation_id,
            ignore_feature_flag=ignore_feature_flag,
        )
