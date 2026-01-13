import json
import threading
import time
from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api_keys.models import MasterAPIKey
from organisations.models import Organisation


# This integration test reproduces a race condition during segment PATCH updates.
# When nested segment rules are deleted before new rules are created, the segment
# can temporarily evaluate as "match all". That causes identities without the
# required traits to receive an enabled feature state from a segment override.
# The test continuously PATCHes the same ruleset while polling identity feature
# states to surface any incorrect, transient enables.
@pytest.mark.django_db(transaction=True)
def test_segment_patch_atomic__looped_repro__detects_mismatch(  # type: ignore[no-untyped-def]
    admin_client,
    admin_user,
    environment,
    environment_api_key,
    feature,
    organisation,
    project,
):
    # Given: a segment that should only match identities with specific traits.
    # The feature override is enabled for that segment, so non-matching
    # identities must always see the feature disabled.
    rules_payload = _build_rules_payload()
    segment_id = _create_segment(
        admin_client=admin_client,
        project_id=project,
        rules_payload=rules_payload,
    )
    feature_segment_id = _create_feature_segment(
        admin_client=admin_client,
        environment_id=environment,
        feature_id=feature,
        segment_id=segment_id,
    )
    _create_feature_segment_override(
        admin_client=admin_client,
        environment_id=environment,
        feature_id=feature,
        feature_segment_id=feature_segment_id,
    )
    identity_id = _create_identity(
        admin_client=admin_client,
        environment_api_key=environment_api_key,
        identifier="disabled-identity",
    )

    # API endpoints under test: segment PATCH and identity feature state listing.
    patch_url = reverse(
        "api-v1:projects:project-segments-detail",
        args=[project, segment_id],
    )
    identity_feature_states_url = reverse(
        "api-v1:environments:identity-featurestates-all",
        args=(environment_api_key, identity_id),
    )

    # Use a master API key for PATCH requests so that concurrent writes
    # are authenticated independently of the admin session client.
    organisation_obj = Organisation.objects.get(id=organisation)
    master_key_data = MasterAPIKey.objects.create_key(  # type: ignore[attr-defined]
        name="test_key",
        organisation=organisation_obj,
        is_admin=True,
    )
    _, master_key = master_key_data
    patch_client = APIClient()
    patch_client.credentials(HTTP_AUTHORIZATION="Api-Key " + master_key)

    # Use an authenticated admin client for polling identity feature states.
    poll_client = APIClient()
    poll_client.force_authenticate(user=admin_user)

    # Shared state used to coordinate the concurrent loops.
    stop_event = threading.Event()
    end_time = time.monotonic() + 10
    patch_errors: list[str] = []
    poll_errors: list[str] = []
    mismatches: list[dict[str, Any]] = []

    def patch_loop() -> None:
        # Repeatedly PATCH the same ruleset to simulate real-world churn in
        # segment updates. This is intended to hit the race window where the
        # rules are temporarily empty.
        while time.monotonic() < end_time and not stop_event.is_set():
            response = patch_client.patch(
                patch_url,
                data=json.dumps(
                    {
                        "name": "Atomic Patch Segment",
                        "rules": rules_payload,
                    }
                ),
                content_type="application/json",
            )
            if response.status_code != status.HTTP_200_OK:
                patch_errors.append(
                    f"Unexpected patch response: {response.status_code}"
                )
                stop_event.set()
                return

    def poll_loop() -> None:
        # Continuously fetch identity feature states while PATCH is running.
        # Any enabled feature for the non-matching identity indicates the
        # segment temporarily evaluated as true.
        while time.monotonic() < end_time and not stop_event.is_set():
            response = poll_client.get(identity_feature_states_url)
            if response.status_code != status.HTTP_200_OK:
                poll_errors.append(
                    f"Unexpected feature states response: {response.status_code}"
                )
                stop_event.set()
                return

            response_json = response.json()
            feature_state = next(
                (
                    feature_state
                    for feature_state in response_json
                    if feature_state["feature"]["id"] == feature
                ),
                None,
            )
            if feature_state is None:
                poll_errors.append("Feature state missing from response")
                stop_event.set()
                return

            if feature_state["enabled"] is True:
                mismatches.append(feature_state)
                stop_event.set()
                return

    # When: execute concurrent PATCH and polling loops for up to 10 seconds.
    patch_thread = threading.Thread(target=patch_loop)
    patch_thread.start()
    poll_loop()
    stop_event.set()
    patch_thread.join(timeout=2)

    # Then: failures indicate either bad API responses or a reproduced mismatch.
    assert not patch_thread.is_alive()
    assert not patch_errors
    assert not poll_errors
    assert not mismatches


def _build_rules_payload() -> list[dict[str, Any]]:
    conditions = [
        {
            "operator": "EQUAL",
            "property": "flagEnabledId",
            "value": f"enabled-{index}",
        }
        for index in range(10)
    ]
    return [
        {
            "type": "ANY",
            "conditions": conditions,
            "rules": [],
        }
    ]


def _create_segment(
    admin_client: APIClient,
    project_id: int,
    rules_payload: list[dict[str, Any]],
) -> int:
    create_segment_url = reverse(
        "api-v1:projects:project-segments-list", args=[project_id]
    )
    response = admin_client.post(
        create_segment_url,
        data=json.dumps(
            {
                "name": "Atomic Patch Segment",
                "project": project_id,
                "rules": rules_payload,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]


def _create_feature_segment(
    admin_client: APIClient,
    environment_id: int,
    feature_id: int,
    segment_id: int,
) -> int:
    create_feature_segment_url = reverse("api-v1:features:feature-segment-list")
    response = admin_client.post(
        create_feature_segment_url,
        data=json.dumps(
            {
                "feature": feature_id,
                "segment": segment_id,
                "environment": environment_id,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]


def _create_feature_segment_override(
    admin_client: APIClient,
    environment_id: int,
    feature_id: int,
    feature_segment_id: int,
) -> None:
    create_feature_state_url = reverse("api-v1:features:featurestates-list")
    response = admin_client.post(
        create_feature_state_url,
        data=json.dumps(
            {
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "segment override",
                },
                "feature": feature_id,
                "environment": environment_id,
                "feature_segment": feature_segment_id,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED


def _create_identity(
    admin_client: APIClient,
    environment_api_key: str,
    identifier: str,
) -> int:
    create_identity_url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment_api_key],
    )
    response = admin_client.post(
        create_identity_url,
        data={"identifier": identifier},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]
