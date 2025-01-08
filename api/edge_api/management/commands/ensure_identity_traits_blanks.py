import json
from argparse import ArgumentParser
from typing import Any

import structlog
from django.core.management import BaseCommand

from environments.dynamodb import DynamoIdentityWrapper

identity_wrapper = DynamoIdentityWrapper()

logger: structlog.BoundLogger = structlog.get_logger()

LOG_COUNT_EVERY = 100_000


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--exclusive-start-key",
            dest="exclusive_start_key",
            type=str,
            default="",
            help="Exclusive start key in valid JSON",
        )

    def handle(self, *args: Any, exclusive_start_key: str, **options: Any) -> None:
        total_count = identity_wrapper.table.item_count
        scanned_count = scanned_percentage = fixed_count = 0

        log: structlog.BoundLogger = logger.bind(total_count=total_count)

        kwargs = {}
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = json.loads(exclusive_start_key)

        log.info("started")

        for identity_document in identity_wrapper.scan_iter_all_items(**kwargs):
            should_write_identity_document = False

            if identity_traits_data := identity_document.get("identity_traits"):
                blank_traits = (
                    trait_data
                    for trait_data in identity_traits_data
                    if "trait_value" not in trait_data
                )
                for trait_data in blank_traits:
                    should_write_identity_document = True
                    trait_data["trait_value"] = ""

            scanned_count += 1
            scanned_percentage = scanned_count / total_count * 100

            if should_write_identity_document:
                identity_wrapper.put_item(identity_document)
                fixed_count += 1

                log.info(
                    "identity-fixed",
                    identity_uuid=identity_document["identity_uuid"],
                    scanned_count=scanned_count,
                    scanned_percentage=scanned_percentage,
                    fixed_count=fixed_count,
                )

            if not (scanned_count % LOG_COUNT_EVERY):
                log.info(
                    "in-progress",
                    scanned_count=scanned_count,
                    scanned_percentage=scanned_percentage,
                    fixed_count=fixed_count,
                )

        log.info(
            "finished",
            scanned_count=scanned_count,
            scanned_percentage=scanned_percentage,
            fixed_count=fixed_count,
        )
