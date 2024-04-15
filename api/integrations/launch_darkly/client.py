from typing import Any, Iterator, Optional, TypeVar

from requests import Session

from integrations.launch_darkly import types as ld_types
from integrations.launch_darkly.constants import (
    LAUNCH_DARKLY_API_BASE_URL,
    LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE,
    LAUNCH_DARKLY_API_VERSION,
)

T = TypeVar("T")


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

    def _get_json_response(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> T:
        full_url = f"{LAUNCH_DARKLY_API_BASE_URL}{endpoint}"
        response = self.client_session.get(full_url, params=params)
        response.raise_for_status()
        return response.json()

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

        response_json = self._get_json_response(
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
