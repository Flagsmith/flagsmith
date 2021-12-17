import requests
import settings


class MailerLite:
    def __init__(self):
        self.url = settings.MAILERLITE_BASE_URL + "subscribers"
        self.headers = {"X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY}

    def subscribe(self, data):
        requests.post(self.url, data=data, headers=self.headers)
