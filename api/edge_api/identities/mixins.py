import json

import requests
from django.conf import settings
from rest_framework.request import Request

from environments.dynamodb import DynamoIdentityWrapper
from util.util import postpone


class MigrateIdentitiesUsingRequestsMixin:
    identities_url = settings.EDGE_API_URL + "/identities/"

    def migrate_identity(self, request: Request, api_key: str, project_id: int):
        if not settings.EDGE_API_URL:
            return
        self._migrate_identity_async(request)

    def _migrate_identity_sync(self, request: Request, api_key: str, project_id: int):
        dynamo_identity_wrapper = DynamoIdentityWrapper()
        if not dynamo_identity_wrapper.is_migration_done(project_id):
            return
        if request.method == "POST":
            return self._make_migrate_identity_post_request(request)
        self._make_migrate_identity_get_request(request)

    @postpone
    def _migrate_identity_async(self, request: Request, api_key: str, project_id: int):
        return self._migrate_identity_sync(request, api_key, project_id)

    def _make_migrate_identity_get_request(self, request: Request, api_key: str):
        return requests.get(
            self.identities_url,
            params=requests.GET.dict(),
            headers=_request_headers(api_key),
        )

    def _make_migrate_identity_post_request(self, request: Request, api_key: str):
        requests.post(
            self.identities_url,
            payload=request.data,
            headers=_request_headers(api_key),
        )


class MigrateTraitsUsingRequestMixin:

    traits_url = settings.EDGE_API_URL + "/traits/"

    def migrate_trait(self, request: Request, payload: dict = None):
        if not settings.EDGE_API_URL:
            return
        self._migrate_trait_async(request, payload)

    def _migrate_trait_sync(self, request: Request, payload: dict = None):
        payload = json.dumps(payload) if payload else request.body
        requests.post(
            self.traits_url,
            payload=payload,
            headers=_request_headers(request.environment.api_key),
        )

    @postpone
    def _migrate_trait_async(self, request: Request, payload: dict = None):
        return self._migrate_trait_sync(request, payload)

    def migrate_trait_bulk(self, request: Request):
        if not settings.EDGE_API_URL:
            return
        return self._migrate_trait_bulk_async(request)

    def _migrate_trait_bulk_sync(self, request: Request):
        for trait in request.body:
            self._migrate_trait_sync(request, trait)

    @postpone
    def _migrate_trait_bulk_async(self, request: Request):
        self._migrate_trait_bulk_sync(request)


def _request_headers(api_key: str) -> dict:
    return {"X-Environment-Key": api_key, "Content-Type": "application/json"}
