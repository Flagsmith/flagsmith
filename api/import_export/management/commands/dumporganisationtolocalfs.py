import json
import logging

from django.core.management import BaseCommand, CommandParser
from django.core.serializers.json import DjangoJSONEncoder

from import_export.export import full_export

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "organisation-id",
            type=int,
            help="Id of the Organisation to dump",
        )
        parser.add_argument(
            "file-location",
            type=str,
            help="Full path to file in which to write organisation data.",
        )

        parser.add_argument(
            "for-self-hosted",
            type=bool,
            default=True,
            help="Indicates whether the dump is intended to be loaded on a self-hosted instance.",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        organisation_id = options["organisation-id"]
        file_location = options["file-location"]
        for_self_hosted = options["for-self-hosted"]

        logger.info("Dumping organisation '%d' to '%s'", organisation_id, file_location)

        with open(file_location, "a+") as output_file:
            output_file.write(
                json.dumps(
                    full_export(organisation_id, for_self_hosted), cls=DjangoJSONEncoder
                )
            )
