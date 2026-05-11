import json

from django.urls import reverse
from django.utils.http import http_date
from rest_framework import status
from rest_framework.test import APIClient


FLAGD_URL = "/api/v1/flagd/flags.json"


def test_flagd_sync__valid_server_key__returns_200_and_document(
    server_side_sdk_client: APIClient,
    environment: int,
    feature: int,
    feature_name: str,
) -> None:
    # Given - the URL for the flagd sync endpoint
    url = reverse("api-v1:flagd:sync")

    # When
    response = server_side_sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["$schema"] == "https://flagd.dev/schema/v0/flags.json"
    assert "flags" in body
    assert body["metadata"]["flagsmith.environmentId"] == environment
    assert body["metadata"]["flagsmith.translatorVersion"] == "v1"
    assert feature_name in body["flags"]


def test_flagd_sync__missing_key__returns_403(
    api_client: APIClient,
    environment: int,
) -> None:
    # Given - no environment key header
    url = reverse("api-v1:flagd:sync")

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_flagd_sync__client_side_key__returns_403(
    sdk_client: APIClient,
    environment: int,
) -> None:
    # Given - a non `ser.`-prefixed (client-side) key on the request
    url = reverse("api-v1:flagd:sync")

    # When
    response = sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_flagd_sync__authorization_bearer_header__returns_200(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
) -> None:
    # Given - a server-side key supplied via Authorization: Bearer <key>
    # (used by the flagd HTTP sync source, which exposes `authHeader`)
    url = reverse("api-v1:environments:api-keys-list", args=[environment_api_key])
    key = admin_client.post(url, data={"name": "flagd"}).json()["key"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {key}")

    # When
    response = client.get(reverse("api-v1:flagd:sync"))

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_flagd_sync__authorization_raw_token__returns_200(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
) -> None:
    # Given - a server-side key supplied as a raw Authorization header value
    url = reverse("api-v1:environments:api-keys-list", args=[environment_api_key])
    key = admin_client.post(url, data={"name": "flagd"}).json()["key"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=key)

    # When
    response = client.get(reverse("api-v1:flagd:sync"))

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_flagd_sync__if_modified_since_matches__returns_304(
    server_side_sdk_client: APIClient,
    environment: int,
) -> None:
    # Given - first request to capture the Last-Modified header
    url = reverse("api-v1:flagd:sync")
    first_response = server_side_sdk_client.get(url)
    assert first_response.status_code == status.HTTP_200_OK
    last_modified = first_response.headers["Last-Modified"]

    # When - second request with matching If-Modified-Since
    second_response = server_side_sdk_client.get(
        url,
        HTTP_IF_MODIFIED_SINCE=last_modified,
    )

    # Then
    assert second_response.status_code == status.HTTP_304_NOT_MODIFIED
    assert len(second_response.content) == 0


def test_flagd_sync__etag_matches__returns_304(
    server_side_sdk_client: APIClient,
    environment: int,
) -> None:
    # Given - first request to capture the ETag header
    url = reverse("api-v1:flagd:sync")
    first_response = server_side_sdk_client.get(url)
    assert first_response.status_code == status.HTTP_200_OK
    etag = first_response.headers["ETag"]
    assert etag

    # When - second request with matching If-None-Match
    second_response = server_side_sdk_client.get(
        url,
        HTTP_IF_NONE_MATCH=etag,
    )

    # Then
    assert second_response.status_code == status.HTTP_304_NOT_MODIFIED
    assert len(second_response.content) == 0


def test_flagd_sync__feature_with_segment_override__document_contains_evaluator(
    server_side_sdk_client: APIClient,
    environment: int,
    feature: int,
    feature_name: str,
    segment: int,
    segment_name: str,
    segment_featurestate: int,
) -> None:
    # Given - a feature with a segment override
    url = reverse("api-v1:flagd:sync")

    # When
    response = server_side_sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()

    # The slugified key for "Test Segment" is "Test-Segment"
    expected_segment_key = "Test-Segment"
    assert "$evaluators" in body
    assert expected_segment_key in body["$evaluators"]

    flag = body["flags"][feature_name]
    targeting = flag["targeting"]
    assert targeting is not None
    # The targeting expression should reference the segment evaluator.
    serialised = json.dumps(targeting)
    assert "$ref" in serialised
    assert expected_segment_key in serialised


def test_flagd_sync__multivariate_flag__variants_and_fractional(
    server_side_sdk_client: APIClient,
    environment: int,
    project: int,
    admin_client: APIClient,
    mv_feature: int,
    mv_feature_name: str,
    mv_feature_option: int,
    mv_feature_option_value: str,
) -> None:
    # Given - the multivariate feature is enabled at the environment level so
    # targeting (and thus the fractional expression) is emitted.
    feature_states_url = reverse("api-v1:features:featurestates-list")
    feature_states_response = admin_client.get(
        feature_states_url,
        {"environment": environment, "feature": mv_feature},
    )
    feature_state = feature_states_response.json()["results"][0]
    feature_state["enabled"] = True
    admin_client.put(
        reverse(
            "api-v1:features:featurestates-detail",
            args=[feature_state["id"]],
        ),
        data=json.dumps(feature_state),
        content_type="application/json",
    )

    # Allocate 100% of identities to the multivariate option so the fractional
    # weight is non-zero and the expression is included in targeting.
    mv_option_url = reverse(
        "api-v1:projects:feature-mv-options-detail",
        args=[project, mv_feature, mv_feature_option],
    )
    mv_option_response = admin_client.get(mv_option_url)
    mv_option_data = mv_option_response.json()
    mv_option_data["default_percentage_allocation"] = 100
    admin_client.put(
        mv_option_url,
        data=json.dumps(mv_option_data),
        content_type="application/json",
    )

    url = reverse("api-v1:flagd:sync")

    # When
    response = server_side_sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    flag = body["flags"][mv_feature_name]

    # The default `on`/`off` variants are always present, plus a variant for
    # the multivariate option value.
    assert "on" in flag["variants"]
    assert "off" in flag["variants"]
    assert mv_feature_option_value in flag["variants"].values()

    # Targeting should be a fractional expression for the enabled flag.
    assert flag["targeting"] is not None
    assert "fractional" in json.dumps(flag["targeting"])


def test_flagd_sync__disabled_flag__state_disabled(
    server_side_sdk_client: APIClient,
    environment: int,
    feature: int,
    feature_name: str,
) -> None:
    # Given - the default `feature` fixture creates a flag with default_enabled=False
    url = reverse("api-v1:flagd:sync")

    # When
    response = server_side_sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["flags"][feature_name]["state"] == "DISABLED"
