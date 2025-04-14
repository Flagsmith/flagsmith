import logging

from django.core.management import BaseCommand, CommandParser

from import_export.export import S3OrganisationExporter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.exporter = S3OrganisationExporter()  # type: ignore[no-untyped-call]

    def add_arguments(self, parser: CommandParser):  # type: ignore[no-untyped-def]
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
        parser.add_argument(
            "for-self-hosted",
            type=bool,
            default=True,
            help="Indicates whether the dump is intended to be loaded on a self-hosted instance.",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        organisation_id = options["organisation-id"]
        bucket_name = options["bucket-name"]
        for_self_hosted = options["for-self-hosted"]
        key = options["key"]

        logger.info(
            "Dumping organisation '%d' to bucket '%s' and key '%s'",
            organisation_id,
            bucket_name,
            key,
        )

        self.exporter.export_to_s3(organisation_id, bucket_name, key, for_self_hosted)
