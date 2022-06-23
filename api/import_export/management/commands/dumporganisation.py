import json

from django.core.management import BaseCommand, CommandParser
from django.core.serializers.json import DjangoJSONEncoder

from import_export.export import (
    export_environments,
    export_features,
    export_identities,
    export_organisation,
    export_projects,
)


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "organisation_id",
            type=int,
            help="Id of the Organisation to dump",
        )

    def handle(self, *args, **options):
        organisation_id = options["organisation_id"]
        with open("./dumpdata_mgmt.json", "w") as f:
            data = export_organisation(organisation_id)
            data += export_projects(organisation_id)
            data += export_environments(organisation_id)
            data += export_identities(organisation_id)
            data += export_features(organisation_id)
            f.write(json.dumps(data, cls=DjangoJSONEncoder))
