from django.core.management.base import BaseCommand

from environments.dynamodb import DynamoIdentityWrapper


class Command(BaseCommand):
    help = "Migrate Identity Data to Dynamo db"

    def add_arguments(self, parser):
        parser.add_argument(
            "project", type=int, help="Id of the project being migrated"
        )

    def handle(self, *args, **options):
        project_id = options["project"]
        dynamo_wrapper = DynamoIdentityWrapper()
        dynamo_wrapper.migrate_identities(project_id)
