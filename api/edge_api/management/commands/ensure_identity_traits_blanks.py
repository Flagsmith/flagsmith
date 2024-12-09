import logging
from typing import Any

from django.core.management import BaseCommand

from environments.dynamodb import DynamoIdentityWrapper

identity_wrapper = DynamoIdentityWrapper()


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        for identity_document in identity_wrapper.query_get_all_items():
            should_write_identity_document = False
            if identity_traits_data := identity_document.get("identity_traits"):
                for trait_data in identity_traits_data:
                    if "trait_value" not in trait_data:
                        should_write_identity_document = True
                        trait_data["trait_value"] = ""
            if should_write_identity_document:
                identity_wrapper.put_item(identity_document)
                self.stdout.write(
                    f"Fixed identity id={identity_document['identity_uuid']}",
                )
        self.stdout.write(self.style.SUCCESS("Finished."))
