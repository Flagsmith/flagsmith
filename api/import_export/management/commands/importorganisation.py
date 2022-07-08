from django.core.management import BaseCommand, CommandParser

from import_export.import_ import OrganisationImporter


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.importer = OrganisationImporter()

    def add_arguments(self, parser: CommandParser):
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

    def handle(self, *args, **options):
        bucket_name = options["bucket-name"]
        key = options["key"]

        self.importer.import_organisation(bucket_name, key)
