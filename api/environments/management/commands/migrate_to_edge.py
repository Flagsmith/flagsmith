import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from flag_engine.django_transform.document_builders import (
    build_identity_document,
)

from projects.models import Project


class Command(BaseCommand):
    help = "Migrate Identity Data to Dynamo db"

    def add_arguments(self, parser):
        parser.add_argument(
            "project", type=int, help="Id of the project being migrated"
        )

    def handle(self, *args, **options):
        if not settings.IDENTITIES_TABLE_NAME_DYNAMO:
            raise CommandError(
                "Environment variable IDENTITIES_TABLE_NAME_DYNAMO is not set"
            )
        identity_table = boto3.resource("dynamodb").Table(
            settings.IDENTITIES_TABLE_NAME_DYNAMO
        )
        project_id = options["project"]
        for environment in Project.objects.get(id=project_id).environments.all():
            with identity_table.batch_writer() as batch:
                for identity in environment.identities.all():
                    identity_document = build_identity_document(identity)
                    print(identity.id)
                    batch.put_item(Item=identity_document)
