import json

import requests
from django.conf import settings
from rest_framework.request import Request

from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from util.util import postpone


def _should_migrate(project_id: int) -> bool:
    if not settings.EDGE_API_URL:
        return False
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    return dynamo_identity_wrapper.is_migration_done(project_id)


class MigrateIdentitiesUsingRequestsMixin:
    identities_url = settings.EDGE_API_URL + "identities/"

    def migrate_identity(self, request: Request, environment):
        self._migrate_identity_async(request, environment)

    @postpone
    def _migrate_identity_async(self, request: Request, environment: Environment):
        return self._migrate_identity_sync(request, environment)

    def _migrate_identity_sync(self, request: Request, environment: Environment):
        if not _should_migrate(environment.project.id):
            return
        if request.method == "POST":
            return self._make_migrate_identity_post_request(
                request, environment.api_key
            )
        self._make_migrate_identity_get_request(request, environment.api_key)

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

    def migrate_trait(
        self, request: Request, environment: Environment, payload: dict = None
    ):
        self._migrate_trait_async(request, environment, payload)

    @postpone
    def _migrate_trait_async(
        self, request: Request, environment: Environment, payload: dict = None
    ):
        return self._migrate_trait_sync(request, environment, payload)

    def _migrate_trait_sync(
        self, request: Request, environment: Environment, payload: dict = None
    ):
        if not _should_migrate(environment.project.id):
            return
        payload = payload if payload else request.data
        requests.post(
            self.traits_url,
            data=json.dumps(payload),
            headers=_request_headers(environment.api_key),
        )

    def migrate_trait_bulk(self, request: Request, environment: Environment):
        return self._migrate_trait_bulk_async(request, environment)

    @postpone
    def _migrate_trait_bulk_async(self, request: Request, environment: Environment):
        self._migrate_trait_bulk_sync(request, environment)

    def _migrate_trait_bulk_sync(self, request: Request, environment: Environment):
        for trait in request.data:
            self._migrate_trait_sync(request, environment, trait)


def _request_headers(api_key: str) -> dict:
    return {"X-Environment-Key": api_key, "Content-Type": "application/json"}
