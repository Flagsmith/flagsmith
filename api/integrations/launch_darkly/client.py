from datetime import timedelta
from typing import Any, Callable, Generator, Iterator, Optional, TypeVar

import backoff
from backoff.types import Details
from django.utils.timezone import now as timezone_now
from requests import RequestException, Session
from rest_framework.status import HTTP_429_TOO_MANY_REQUESTS

from integrations.launch_darkly import types as ld_types
from integrations.launch_darkly.constants import (
    BACKOFF_DEFAULT_RETRY_AFTER_SECONDS,
    BACKOFF_MAX_RETRIES,
    LAUNCH_DARKLY_API_BASE_URL,
    LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE,
    LAUNCH_DARKLY_API_VERSION,
)
from integrations.launch_darkly.exceptions import LaunchDarklyRateLimitError

T = TypeVar("T")


def launch_darkly_backoff(
    _get_json_response: Callable[..., T],
) -> Callable[..., T]:
    # Handle LaunchDarkly rate limiting according to their API documentation:
    # https://launchdarkly.com/docs/api
    #
    # 1. If a request returns a 429 Too Many Requests status code, the client should back off.
    # 2. When backing off, the client retries the request after the time specified in the `Retry-After` header
    #   or the `X-Ratelimit-Reset` header, if present, or a default of `BACKOFF_DEFAULT_RETRY_SECONDS`.
    # 3. After `BACKOFF_MAX_RETRIES` retries, we give up.
    #   If the last error was a 429 and contained retry information,
    #   signal for the import request to be retried later by raising a `LaunchDarklyRateLimitError`.

    def _get_retry_after(exc: RequestException) -> float | None:
        if (
            (response := exc.response) is not None
        ) and response.status_code == HTTP_429_TOO_MANY_REQUESTS:
            headers = response.headers
            # Clients must wait at least `Retry-After` seconds
            # before making additional calls to the API
            if retry_after := headers.get("Retry-After"):
                return float(retry_after)
            # The time at which the current rate limit window resets in epoch milliseconds
            if ratelimit_reset := headers.get("X-Ratelimit-Reset"):
                timestamp = int(ratelimit_reset) / 1000
                # Use default backoff time if the timestamp is in the past.
                return (
                    max(timestamp - timezone_now().timestamp(), 0)
                    or BACKOFF_DEFAULT_RETRY_AFTER_SECONDS
                )
            # If no retry information retrieved, use a default backoff time
            # of 10 seconds as per LD documentation.
            return BACKOFF_DEFAULT_RETRY_AFTER_SECONDS
        return None

    def _wait_gen() -> Generator[float, None, None]:
        exc: RequestException = yield  # type: ignore[misc,assignment]

        while True:
            if retry_after := _get_retry_after(exc):
                yield retry_after
            else:
                return

    def _handle_giveup(
        details: Details,
    ) -> None:
        exc: RequestException = details["exception"]  # type: ignore[typeddict-item]

        if retry_after := _get_retry_after(exc):
            raise LaunchDarklyRateLimitError(
                retry_at=timezone_now() + timedelta(seconds=retry_after)
            )

        raise exc

    return backoff.on_exception(
        wait_gen=_wait_gen,
        exception=RequestException,
        jitter=backoff.random_jitter,
        on_giveup=_handle_giveup,
        max_tries=BACKOFF_MAX_RETRIES,
    )(_get_json_response)


class LaunchDarklyClient:
    def __init__(self, token: str) -> None:
        client_session = Session()
        client_session.headers.update(
            {
                "Authorization": token,
                "LD-API-Version": LAUNCH_DARKLY_API_VERSION,
            }
        )
        self.client_session = client_session

    @launch_darkly_backoff
    def _get_json_response(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> T:  # type: ignore[type-var]
        full_url = f"{LAUNCH_DARKLY_API_BASE_URL}{endpoint}"
        response = self.client_session.get(full_url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def _iter_paginated_items(
        self,
        collection_endpoint: str,
        additional_params: Optional[dict[str, Any]] = None,
        use_legacy_offset_pagination: bool = False,
    ) -> Iterator[T]:
        """
        Iterator over paginated items in the given collection endpoint.

        :param collection_endpoint: endpoint to get the collection of items
        :param additional_params: Additional parameters to include in the request
        :param use_legacy_offset_pagination: Whether to use offset based pagination if `next` links do not
        exist in the response. Some endpoints do not have `next` links and require offset based pagination.
        :return: Iterator over the items in the collection
        """
        params = {"limit": LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE}
        offset = 0
        if additional_params:
            params.update(additional_params)

        response_json: dict[str, Any] = self._get_json_response(
            endpoint=collection_endpoint,
            params=params,
        )
        while True:
            items = response_json.get("items") or []
            yield from items
            links: Optional[dict[str, ld_types.Link]] = response_json.get("_links")
            if (
                links
                and (next_link := links.get("next"))
                and (next_endpoint := next_link.get("href"))
            ):
                # Don't specify params here because links.next.href includes the
                # original limit and calculates offsets accordingly.
                response_json = self._get_json_response(
                    endpoint=next_endpoint,
                )
            elif use_legacy_offset_pagination and len(items) == params["limit"]:
                # Offset based pagination
                offset += params["limit"]
                params["offset"] = offset
                response_json = self._get_json_response(
                    endpoint=collection_endpoint,
                    params=params,
                )
            else:
                return

    def get_project(self, project_key: str) -> ld_types.Project:
        """operationId: getProject"""
        endpoint = f"/api/v2/projects/{project_key}"
        return self._get_json_response(
            endpoint=endpoint, params={"expand": "environments"}
        )

    def get_environments(self, project_key: str) -> list[ld_types.Environment]:
        """operationId: getEnvironmentsByProject"""
        endpoint = f"/api/v2/projects/{project_key}/environments"
        return list(
            self._iter_paginated_items(
                collection_endpoint=endpoint,
            )
        )

    def get_flags(self, project_key: str) -> list[ld_types.FeatureFlag]:
        """operationId: getFeatureFlags"""
        endpoint = f"/api/v2/flags/{project_key}"
        return list(
            self._iter_paginated_items(
                collection_endpoint=endpoint,
                # Summary should be set to 0 in order to get the full flag data including rules.
                # https://apidocs.launchdarkly.com/tag/Feature-flags#operation/getFeatureFlags!in=query&path=summary&t=request
                additional_params={"summary": "0"},
            )
        )

    def get_flag_count(self, project_key: str) -> int:
        """operationId: getFeatureFlags

        Request minimal info and return the total flag count.
        """
        endpoint = f"/api/v2/flags/{project_key}"
        flags: ld_types.FeatureFlags = self._get_json_response(
            endpoint=endpoint,
            params={"limit": 1},
        )
        return flags["totalCount"]

    def get_flag_tags(self) -> list[str]:
        """operationId: getTags"""
        endpoint = "/api/v2/tags"
        return list(
            self._iter_paginated_items(
                collection_endpoint=endpoint,
                additional_params={"kind": "flag"},
            )
        )

    def get_segment_tags(self) -> list[str]:
        """operationId: getTags"""
        endpoint = "/api/v2/tags"
        return list(
            self._iter_paginated_items(
                collection_endpoint=endpoint,
                additional_params={"kind": "segment"},
            )
        )

    def get_segments(
        self, project_key: str, environment_key: str
    ) -> list[ld_types.UserSegment]:
        """operationId: getSegments"""
        endpoint = f"/api/v2/segments/{project_key}/{environment_key}"
        return list(
            self._iter_paginated_items(
                collection_endpoint=endpoint,
                additional_params={"limit": 50},
                use_legacy_offset_pagination=True,
            )
        )

    def get_segment(
        self, project_key: str, environment_key: str, segment_key: str
    ) -> ld_types.UserSegment:
        """operationId: getSegment"""
        endpoint = f"/api/v2/segments/{project_key}/{environment_key}/{segment_key}"
        return self._get_json_response(endpoint=endpoint)
