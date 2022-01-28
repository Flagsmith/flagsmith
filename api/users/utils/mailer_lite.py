import json
import typing
from contextlib import AbstractContextManager

import requests
from django.conf import settings

from users import models
from util.util import postpone

DEFAULT_MAX_BATCH_SIZE = 50


class MailerLiteBaseClient:
    resource = None
    request_headers = {
        "X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY,
        "Content-Type": "application/json",
    }

    def __init__(self):
        self.base_url = settings.MAILERLITE_BASE_URL

    def _post(self, data):
        url = self.base_url + self.resource
        requests.post(url, data=json.dumps(data), headers=self.request_headers)


class MailerLite(MailerLiteBaseClient):
    resource = f"groups/{settings.MAILERLITE_NEW_USER_GROUP_ID}/subscribers"

    @postpone
    def subscribe(self, user: "models.FFAdminUser"):
        self._subscribe(user)

    @postpone
    def update_organisation_users(self, organisation_id: int):
        return self._update_organisation_users(organisation_id)

    def _subscribe(self, user: "models.FFAdminUser"):
        if not user.marketing_consent_given:
            return
        data = _get_request_body_from_user(user)
        self._post(data)

    def _update_organisation_users(self, organisation_id: int):
        users = models.FFAdminUser.objects.filter(
            organisations__id=organisation_id, marketing_consent_given=True
        )
        with BatchSubscribe() as batch:
            for user in users:
                batch.subscribe(user)


class BatchSubscribe(MailerLiteBaseClient, AbstractContextManager):
    resource = "batch"

    def __init__(self, max_batch_size: int = DEFAULT_MAX_BATCH_SIZE):
        super().__init__()
        self._batch = []
        self.max_batch_size = max_batch_size

    def _get_raw_subscribe_request(self, user):
        return {
            "method": "POST",
            "path": "/api/v2/subscribers",
            "body": _get_request_body_from_user(user),
        }

    def batch_send(self):
        data = {"requests": self._batch}
        self._post(data)
        self._batch.clear()

    def subscribe(self, user: "models.FFAdminUser"):
        if len(self._batch) >= self.max_batch_size:
            self.batch_send()
        self._batch.append(self._get_raw_subscribe_request(user))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.batch_send()


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
