from typing import Any, Iterator, Optional

from requests import Session

from integrations.launch_darkly import types as ld_types

LAUNCH_DARKLY_API_BASE_URL = "https://app.launchdarkly.com"
LAUNCH_DARKLY_API_VERSION = "20220603"
# Maximum limit for /api/v2/projects/
# /api/v2/flags/ seemingly not limited, but let's not get too greedy
LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE = 1000


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
    ) -> dict[str, Any]:
        full_url = f"{LAUNCH_DARKLY_API_BASE_URL}{endpoint}"
        response = self.client_session.get(full_url, params=params)
        response.raise_for_status()
        return response.json()

    def _iter_paginated_items(
        self,
        collection_endpoint: str,
        additional_params: Optional[dict[str, str]] = None,
    ) -> Iterator[dict[str, Any]]:
        params = {"limit": LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE}
        if additional_params:
            params.update(additional_params)

        response_json = self._get_json_response(
            endpoint=collection_endpoint,
            params=params,
        )
        while True:
            yield from response_json.get("items") or []
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
