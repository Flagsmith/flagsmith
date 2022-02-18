import json

import requests
from django.conf import settings
from rest_framework.request import Request

from environments.dynamodb import DynamoIdentityWrapper
from util.util import postpone


class MigrateIdentitiesUsingRequestsMixin:
    identities_url = settings.EDGE_API_URL + "identities/"

    def migrate_identity(self, request: Request, environment):
        if not settings.EDGE_API_URL:
            return
        self._migrate_identity_async(
            request, environment.api_key, environment.project.id
        )

    def _migrate_identity_sync(self, request: Request, api_key: str, project_id: int):
        dynamo_identity_wrapper = DynamoIdentityWrapper()
        if not dynamo_identity_wrapper.is_migration_done(project_id):
            return
        if request.method == "POST":
            return self._make_migrate_identity_post_request(request, api_key)
        self._make_migrate_identity_get_request(request, api_key)

    @postpone
    def _migrate_identity_async(self, request: Request, api_key: str, project_id: int):
        return self._migrate_identity_sync(request, api_key, project_id)

    def _make_migrate_identity_get_request(self, request: Request, api_key: str):
        return requests.get(
            self.identities_url,
            params=request.GET.dict(),
            headers=_request_headers(api_key),
        )

    def _make_migrate_identity_post_request(self, request: Request, api_key: str):
        requests.post(
            self.identities_url,
            data=json.dumps(request.data),
            headers=_request_headers(api_key),
        )


class MigrateTraitsUsingRequestMixin:

    traits_url = settings.EDGE_API_URL + "traits/"

    def migrate_trait(self, request: Request, environment, payload: dict = None):
        if not settings.EDGE_API_URL:
            return
        dynamo_identity_wrapper = DynamoIdentityWrapper()
        if not dynamo_identity_wrapper.is_migration_done(environment.project_id):
            return
        self._migrate_trait_async(request, payload)

    def _migrate_trait_sync(self, request: Request, api_key: str, payload: dict = None):
        payload = payload if payload else request.data
        requests.post(
            self.traits_url,
            data=json.dumps(payload),
            headers=_request_headers(api_key),
        )

    @postpone
    def _migrate_trait_async(
        self, request: Request, api_key: str, payload: dict = None
    ):
        return self._migrate_trait_sync(request, payload)

    def migrate_trait_bulk(self, request: Request, environment):
        if not settings.EDGE_API_URL:
            return
        return self._migrate_trait_bulk_async(request, environment.api_key)

    def _migrate_trait_bulk_sync(self, request: Request, api_key: str):
        for trait in request.data:
            self._migrate_trait_sync(request, api_key, trait)

    @postpone
    def _migrate_trait_bulk_async(self, request: Request, api_key: str):
        self._migrate_trait_bulk_sync(request, api_key)


def _request_headers(api_key: str) -> dict:
    return {"X-Environment-Key": api_key, "Content-Type": "application/json"}
