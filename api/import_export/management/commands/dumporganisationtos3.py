import logging

from django.core.management import BaseCommand, CommandParser

from import_export.export import S3OrganisationExporter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exporter = S3OrganisationExporter()

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "organisation-id",
            type=int,
            help="Id of the Organisation to dump",
        )
        parser.add_argument(
            "bucket-name",
            type=str,
            help="Name of the s3 bucket to export to.",
        )
        parser.add_argument(
            "key",
            type=str,
            help="S3 key to export to.",
        )

    def handle(self, *args, **options):
        organisation_id = options["organisation-id"]
        bucket_name = options["bucket-name"]
        key = options["key"]

        logger.info(
            "Dumping organisation '%d' to bucket '%s' and key '%s'",
            organisation_id,
            bucket_name,
            key,
        )

        self.exporter.export_to_s3(organisation_id, bucket_name, key)
