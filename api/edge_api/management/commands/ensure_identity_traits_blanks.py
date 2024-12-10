from typing import Any

from django.core.management import BaseCommand
from structlog import get_logger
from structlog.stdlib import BoundLogger

from environments.dynamodb import DynamoIdentityWrapper

identity_wrapper = DynamoIdentityWrapper()


LOG_COUNT_EVERY = 100_000


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        total_count = identity_wrapper.table.item_count
        scanned_count = 0
        fixed_count = 0

        log: BoundLogger = get_logger(total_count=total_count)
        log.info("started")

        for identity_document in identity_wrapper.query_get_all_items():
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
