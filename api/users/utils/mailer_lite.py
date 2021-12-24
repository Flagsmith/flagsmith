import json
import typing
from contextlib import AbstractContextManager

import requests
from django.conf import settings

from users import models
from util.util import postpone

MAX_BATCH_SIZE = 50


class MailerLite:
    def __init__(self):
        self.url = settings.MAILERLITE_BASE_URL + "subscribers"

    @postpone
    def subscribe(self, user: "models.FFAdminUser"):
        self._subscribe(user)

    @postpone
    def subcribe_organisation(self, organisation_id: int):
        return self._subcribe_organisation(organisation_id)

    def _subscribe(self, user: "models.FFAdminUser"):
        if not user.is_subscribed:
            return
        payload = json.dumps(_get_request_body_from_user(user))
        requests.post(self.url, data=payload, headers=_get_request_headers())

    def _subcribe_organisation(self, organisation_id: int):
        users = models.FFAdminUser.objects.filter(
            organisations__id=organisation_id, is_subscribed=True
        )
        with BatchSubscribe() as batch:
            for user in users:
                batch.subscribe(user)


class BatchSubscribe(AbstractContextManager):
    def __init__(self):
        self.url = settings.MAILERLITE_BASE_URL + "batch"
        self._batch = []

    def _get_raw_subscribe_request(self, user):
        return {
            "method": "POST",
            "path": "/api/v2/subscribers",
            "body": _get_request_body_from_user(user),
        }

    def _batch_send(self):
        payload = json.dumps({"requests": self._batch})
        requests.post(self.url, data=payload, headers=_get_request_headers())
        self._batch.clear()

    def subscribe(self, user: "models.FFAdminUser"):
        if len(self._batch) >= MAX_BATCH_SIZE:
            self._batch_send()
        self._batch.append(self._get_raw_subscribe_request(user))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._batch_send()


def _get_request_headers() -> typing.Mapping:
    return {
        "X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY,
        "Content-Type": "application/json",
    }


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
