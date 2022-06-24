import json
from datetime import datetime

from django.core.management import BaseCommand, CommandParser
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from import_export.export import full_export


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "organisation-id",
            type=int,
            help="Id of the Organisation to dump",
        )
        parser.add_argument(
            "output-dir",
            type=str,
            help="Directory path to output json file.",
        )
        parser.add_argument(
            "--output-filename",
            type=str,
            help="Filename of JSON output.",
        )

    def handle(self, *args, **options):
        organisation_id = options["organisation-id"]

        output_filepath = options["output-dir"]
        if not output_filepath.endswith("/"):
            output_filepath += "/"
        if options.get("output-filename"):
            output_filepath += options["output-filename"]
        else:
            output_filepath += "flagsmith-org-export-%s-%s.json" % (
                organisation_id,
                datetime.strftime(timezone.now(), "%Y%m%d%H%M%S%f"),
            )

        with open(output_filepath, "w") as f:
            f.write(json.dumps(full_export(organisation_id), cls=DjangoJSONEncoder))
