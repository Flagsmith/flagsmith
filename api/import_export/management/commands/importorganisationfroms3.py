import logging

from django.core.management import BaseCommand, CommandParser

from import_export.import_ import OrganisationImporter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super(Command, self).__init__(*args, **kwargs)
        self.importer = OrganisationImporter()  # type: ignore[no-untyped-call]

    def add_arguments(self, parser: CommandParser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "bucket-name",
            type=str,
            help="Name of the S3 bucket to get the organisation data from.",
        )
        parser.add_argument(
            "key",
            type=str,
            help="S3 location key to retrieve the organisation data from.",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        bucket_name = options["bucket-name"]
        key = options["key"]

        logger.info(
            "Importing organisation from bucket '%s' with key '%s'", bucket_name, key
        )

        self.importer.import_organisation(bucket_name, key)
