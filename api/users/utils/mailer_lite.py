from typing import Mapping

import requests
from django.conf import settings

from util.util import postpone


class MailerLite:
    def __init__(self):
        self.url = settings.MAILERLITE_BASE_URL + "subscribers"
        self.headers = {"X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY}

    @postpone
    def subscribe(self, data: Mapping):
        requests.post(self.url, data=data, headers=self.headers)
