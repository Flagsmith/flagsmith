import json
import logging

from django.core.management import BaseCommand, CommandParser
from django.core.serializers.json import DjangoJSONEncoder

from import_export.export import full_export

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):
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

    def handle(self, *args, **options):
        organisation_id = options["organisation-id"]
        file_location = options["file-location"]

        logger.info("Dumping organisation '%d' to '%s'", organisation_id, file_location)

        with open(file_location, "a+") as output_file:
            output_file.write(
                json.dumps(full_export(organisation_id), cls=DjangoJSONEncoder)
            )
