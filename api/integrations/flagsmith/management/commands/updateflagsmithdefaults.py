import json
import os

import requests
from django.conf import settings
from django.core.management import BaseCommand

from integrations.flagsmith.exceptions import FlagsmithIntegrationError


class Command(BaseCommand):
    _FLAGS_URL = f"{settings.FLAGSMITH_API_URL}/flags"

    def handle(self, *args, **options):
        response = requests.get(
            self._FLAGS_URL,
            headers={"X-Environment-Key": settings.FLAGSMITH_SERVER_KEY},
        )
        if response.status_code != 200:
            raise FlagsmithIntegrationError(
                f"Couldn't get defaults from Flagsmith. Got {response.status_code} response."
            )

        dir_path = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(dir_path, "../../defaults.json"), "w+") as defaults:
            defaults.write(json.dumps(sorted(response.json())))
