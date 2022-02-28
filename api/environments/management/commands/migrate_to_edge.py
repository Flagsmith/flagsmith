from django.core.management.base import BaseCommand, CommandError

from environments.dynamodb import DynamoIdentityWrapper


class Command(BaseCommand):
    help = "Migrate Identity Data to Dynamo db"

    def add_arguments(self, parser):
        parser.add_argument(
            "project", type=int, help="Id of the project being migrated"
        )

    def handle(self, *args, **options):
        project_id = options["project"]
        identity_wrapper = DynamoIdentityWrapper()
        if not identity_wrapper.can_migrate(project_id):
            raise CommandError(
                "Identities migration for this project is either done or is in progress"
            )
        identity_wrapper.migrate_identities(project_id)
