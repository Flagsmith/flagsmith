import json
import typing
from contextlib import AbstractContextManager

import requests
from django.conf import settings

from users import models
from util.util import postpone

MAX_BATCH_SIZE = 50


class MailerLiteBaseClient:
    resource = None

    def __init__(self):
        self.base_url = settings.MAILERLITE_BASE_URL

    def _post(self, data):
        url = self.base_url + self.resource
        requests.post(url, data=json.dumps(data), headers=self._get_request_headers())

    @staticmethod
    def _get_request_headers() -> typing.Mapping:
        return {
            "X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY,
            "Content-Type": "application/json",
        }


class MailerLite(MailerLiteBaseClient):
    resource = "subscribers"

    @postpone
    def subscribe(self, user: "models.FFAdminUser"):
        self._subscribe(user)

    @postpone
    def subscribe_organisation(self, organisation_id: int):
        return self._subscribe_organisation(organisation_id)

    def _subscribe(self, user: "models.FFAdminUser"):
        if not user.is_subscribed:
            return
        data = _get_request_body_from_user(user)
        self._post(data)

    def _subscribe_organisation(self, organisation_id: int):
        users = models.FFAdminUser.objects.filter(
            organisations__id=organisation_id, is_subscribed=True
        )
        with BatchSubscribe() as batch:
            for user in users:
                batch.subscribe(user)


class BatchSubscribe(MailerLiteBaseClient, AbstractContextManager):
    resource = "batch"

    def __init__(self):
        super().__init__()
        self._batch = []

    def _get_raw_subscribe_request(self, user):
        return {
            "method": "POST",
            "path": "/api/v2/subscribers",
            "body": _get_request_body_from_user(user),
        }

    def _batch_send(self):
        data = {"requests": self._batch}
        self._post(data)
        self._batch.clear()

    def subscribe(self, user: "models.FFAdminUser"):
        if len(self._batch) >= MAX_BATCH_SIZE:
            self._batch_send()
        self._batch.append(self._get_raw_subscribe_request(user))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._batch_send()


def _get_request_body_from_user(user: "models.FFAdminUser") -> typing.Mapping:
    """Returns request body/payload for /subscribe request"""
    return {
        "email": user.email,
        "name": user.get_full_name(),
        "fields": {
            "is_paid": user.organisations.filter(
                subscription__cancellation_date=None
            ).exists()
        },
    }


mailer_lite = MailerLite()
