import logging
from typing import Any

from django.core.management import BaseCommand

from environments.dynamodb import DynamoIdentityWrapper

identity_wrapper = DynamoIdentityWrapper()


LOG_COUNT_EVERY = 100_000


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        total_count = identity_wrapper.table.item_count
        scanned_count = 0

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

            if should_write_identity_document:
                identity_wrapper.put_item(identity_document)
                self.stdout.write(
                    "fixed identity"
                    f"scanned={scanned_count}/{total_count}"
                    f"percentage={scanned_count/total_count*100:.2f}"
                    f"id={identity_document['identity_uuid']}",
                )

            if not (scanned_count % LOG_COUNT_EVERY):
                self.stdout.write(
                    f"scanned={scanned_count}/{total_count}"
                    f"percentage={scanned_count/total_count*100:.2f}"
                )
        self.stdout.write(self.style.SUCCESS("Finished."))
