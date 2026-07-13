"""
Regression tests for the opt-in `include_scheduled` extension to the SDK
environment-document mapper (`util/mappers/engine.py`), covering both
mechanisms by which a change can be scheduled: a future `FeatureState`/
`EnvironmentFeatureVersion` that already exists in the DB, and a committed
but not-yet-materialised `VersionChangeSet` diff.
"""

import datetime
import json
from typing import Any

import pytest
from django.utils import timezone

from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion, VersionChangeSet
from features.versioning.tasks import enable_v2_versioning
from features.workflows.core.models import ChangeRequest
from segments.models import Segment
from users.models import FFAdminUser
from util.mappers.sdk import map_environment_to_sdk_document


@pytest.fixture()
def environment_v2(environment: Environment) -> Environment:
    enable_v2_versioning(environment.id)
    environment.refresh_from_db()
    return environment


def _make_live_feature_state(
    environment: Environment,
    feature: Feature,
    *,
    enabled: bool,
) -> FeatureState:
    """
    By the time this runs, Feature-creation has already auto-cloned a
    default FeatureState into every environment of its project, and — since
    `environment_v2` enables v2 versioning first — that clone is already
    wrapped in its own initial, published EnvironmentFeatureVersion. Edit it
    in place: creating a *second* EnvironmentFeatureVersion here would
    collide, since `add_existing_feature_states` (a post_save receiver on
    EnvironmentFeatureVersion) auto-clones the existing live FeatureState
    into any newly created version, and a second explicit create() call
    would then duplicate it.
    """
    feature_state: FeatureState = FeatureState.objects.get(
        environment=environment,
        feature=feature,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    feature_state.enabled = enabled
    feature_state.save()
    return feature_state


def _make_future_feature_state(
    environment: Environment,
    feature: Feature,
    *,
    enabled: bool,
    live_from: datetime.datetime,
    publish: bool = True,
) -> FeatureState:
    """
    Creating a new EnvironmentFeatureVersion auto-clones the current live
    FeatureState into it (same receiver as `_make_live_feature_state`'s
    docstring explains) — edit that auto-clone rather than calling
    `FeatureState.clone()` again, which would add a second, competing
    FeatureState to the same version.

    With `publish=False` the version stays an unpublished draft, with
    `live_from` set directly on it — the model field is plain-writable and
    the versioning API accepts it at draft-create time, so this is a state
    reachable through the public API, not a test contrivance.
    """
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )
    feature_state: FeatureState = FeatureState.objects.get(
        environment=environment,
        feature=feature,
        environment_feature_version=version,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    feature_state.enabled = enabled
    feature_state.save()
    if publish:
        version.publish(live_from=live_from)
    else:
        version.live_from = live_from
        version.save()
    return feature_state


def _get_feature_state(document: dict[str, Any], feature_id: int) -> dict[str, Any]:
    for feature_state in document["feature_states"]:
        if feature_state["feature"]["id"] == feature_id:
            return feature_state  # type: ignore[no-any-return]
    raise AssertionError(f"no feature state found for feature {feature_id}")


def _get_scheduled_change(
    document: dict[str, Any], feature_id: int
) -> dict[str, Any] | None:
    # `scheduled_change` is omitted from the dump entirely when unpopulated
    # (FeatureStateModel's model_serializer pops the None-valued key to keep
    # the shape upstream-identical), so `.get` here tolerates absence; the
    # default-path tests additionally assert outright that the key is absent.
    return _get_feature_state(document, feature_id).get("scheduled_change")


def _get_segment_scheduled_change(
    document: dict[str, Any], feature_id: int, segment_id: int
) -> dict[str, Any] | None:
    for segment in document["project"]["segments"]:
        if segment["id"] != segment_id:
            continue
        for feature_state in segment["feature_states"]:
            if feature_state["feature"]["id"] == feature_id:
                return feature_state.get("scheduled_change")  # type: ignore[no-any-return]
    raise AssertionError(f"no segment feature state found for feature {feature_id}")


def _bool_value(value: bool) -> dict[str, Any]:
    return {
        "boolean_value": value,
        "integer_value": None,
        "string_value": None,
        "type": "bool",
    }


def _committed_change_request(
    environment: Environment, admin_user: FFAdminUser
) -> ChangeRequest:
    change_request: ChangeRequest = ChangeRequest.objects.create(
        environment=environment, title="scheduled change", user=admin_user
    )
    change_request.committed_at = timezone.now()
    change_request.committed_by = admin_user
    change_request.save()
    return change_request


def _pending_change_set(
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    *,
    live_from: datetime.datetime,
    enabled: bool,
) -> VersionChangeSet:
    change_request = _committed_change_request(environment, admin_user)
    change_set: VersionChangeSet = VersionChangeSet.objects.create(
        environment=environment,
        feature=feature,
        change_request=change_request,
        live_from=live_from,
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": feature.id,
                    "enabled": enabled,
                    "feature_state_value": _bool_value(enabled),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )
    return change_set


# -- FeatureState-based scheduled change --------------------------------------
# Covers a future FeatureState that already exists in the DB (created via
# `EnvironmentFeatureVersion.publish(live_from=<future>)`) — the original,
# minimal-scope implementation.


def test_scheduled_change__not_opted_in__is_never_populated(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given a published, future-scheduled version exists
    _make_live_feature_state(environment_v2, feature, enabled=False)
    _make_future_feature_state(
        environment_v2,
        feature,
        enabled=True,
        live_from=timezone.now() + datetime.timedelta(hours=1),
    )

    # When mapped without opting in
    document = map_environment_to_sdk_document(environment_v2)

    # Then the response shape is byte-for-byte unchanged from upstream:
    # the `scheduled_change` key must not be present at all (not even
    # as an explicit null — upstream has no such field)
    assert "scheduled_change" not in _get_feature_state(document, feature.id)


def test_scheduled_change__future_feature_state_exists__is_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given a published, future-scheduled version exists
    _make_live_feature_state(environment_v2, feature, enabled=False)
    live_from = timezone.now() + datetime.timedelta(hours=1)
    future_fs = _make_future_feature_state(
        environment_v2, feature, enabled=True, live_from=live_from
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the future feature state is surfaced as the scheduled change
    scheduled_change = _get_scheduled_change(document, feature.id)
    assert scheduled_change is not None
    assert scheduled_change["enabled"] == future_fs.enabled
    assert scheduled_change["live_from"] == live_from


def test_scheduled_change__live_from_in_past__is_not_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    """
    A change whose live_from has already elapsed should no longer read as
    "scheduled" even if a background task never actually promoted it to
    the current live version (e.g. task-processor was down).
    """
    # Given a future-scheduled version whose live_from has already elapsed
    _make_live_feature_state(environment_v2, feature, enabled=False)
    _make_future_feature_state(
        environment_v2,
        feature,
        enabled=True,
        live_from=timezone.now() - datetime.timedelta(minutes=1),
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then it is no longer surfaced as a scheduled change
    assert _get_scheduled_change(document, feature.id) is None


def test_scheduled_change__unpublished_draft_version__is_not_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    """
    An unpublished draft EnvironmentFeatureVersion can carry a future
    `live_from` (it's a writable field at draft-create time) and its
    auto-cloned feature states sit in `environment.feature_states.all()`,
    but until the version is published nothing is locked in — the draft
    must not be advertised to SDKs as a scheduled change.
    """
    # Given an unpublished draft version with a future live_from
    _make_live_feature_state(environment_v2, feature, enabled=False)
    _make_future_feature_state(
        environment_v2,
        feature,
        enabled=True,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        publish=False,
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the draft is not advertised as a scheduled change
    assert _get_scheduled_change(document, feature.id) is None


def test_scheduled_change__soft_deleted_published_version__is_not_surfaced(
    environment_v2: Environment,
    feature: Feature,
) -> None:
    """
    `select_related` on `environment_feature_version` in the document
    builder joins straight onto the FK column, bypassing
    `EnvironmentFeatureVersion`'s soft-delete manager, so a soft-deleted
    version can still come back as "published". Setting `deleted_at` via a
    queryset `.update()` isolates exactly that condition: the model's own
    `.delete()` cascades a `SET_NULL` onto the referencing FeatureState's
    `environment_feature_version_id` (its FK's `on_delete`), which would
    already fall back to the (also-excluding) V1 branch regardless of this
    fix — that's not what's under test here.
    """
    # Given a published future version that then gets soft-deleted without
    # nulling the FeatureState's reference to it
    _make_live_feature_state(environment_v2, feature, enabled=False)
    future_feature_state = _make_future_feature_state(
        environment_v2,
        feature,
        enabled=True,
        live_from=timezone.now() + datetime.timedelta(hours=1),
    )
    version = future_feature_state.environment_feature_version
    assert version is not None
    EnvironmentFeatureVersion.objects.filter(uuid=version.uuid).update(
        deleted_at=timezone.now()
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the cancelled version is not advertised as a scheduled change
    assert _get_scheduled_change(document, feature.id) is None


def test_scheduled_change__v1_committed_future_feature_state__is_surfaced(
    environment: Environment,
    feature: Feature,
) -> None:
    """
    V1 (legacy versioning) happy path: committing a scheduled change
    request assigns the new FeatureState a real version number while its
    `live_from` stays in the future — construct that at-rest shape
    directly. The FeatureState-based mechanism must work for V1, not
    just the v2 cases covered above.
    """
    # Given a committed V1 feature state with a future live_from
    live_from = timezone.now() + datetime.timedelta(hours=1)
    FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=2,
        live_from=live_from,
        enabled=True,
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment, include_scheduled=True)

    # Then it is surfaced as the scheduled change
    scheduled_change = _get_scheduled_change(document, feature.id)
    assert scheduled_change is not None
    assert scheduled_change["enabled"] is True
    assert scheduled_change["live_from"] == live_from


def test_scheduled_change__v1_uncommitted_change_request__is_not_surfaced(
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    """
    V1 sibling of the unpublished-draft leak (CR-SF-v1 H-1): feature
    states belonging to a not-yet-committed change request have
    `version=None` but already carry their target `live_from` — upstream
    relies on this at commit time, when
    `features/workflows/core/models.py` compares `committed_at <
    feature_state.live_from` to decide whether the change is scheduled.
    Until the CR is committed nothing is locked in, so the draft must
    not be advertised to SDKs as a scheduled change.
    """
    # Given a V1 feature state tied to a not-yet-committed change request
    change_request = ChangeRequest.objects.create(
        environment=environment, title="draft v1 change", user=admin_user
    )
    FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=None,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        enabled=True,
        change_request=change_request,
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment, include_scheduled=True)

    # Then it is not advertised as a scheduled change, and the live default
    # is served untouched
    assert _get_scheduled_change(document, feature.id) is None
    assert _get_feature_state(document, feature.id)["enabled"] is False


# -- VersionChangeSet-based scheduled change ----------------------------------
# Covers a change-request-scheduled change that has NOT been materialised
# into a real FeatureState yet — it only exists as a `VersionChangeSet`
# JSON diff, per the actual mechanism used by the versioning REST API
# (`features/versioning/serializers.py::VersionChangeSetSerializer.create`)
# when a change request with a future live_from is committed.


def test_scheduled_change__pending_committed_change_set__is_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given a committed change request with a pending, not-yet-materialised
    # VersionChangeSet
    _make_live_feature_state(environment_v2, feature, enabled=False)
    change_request = _committed_change_request(environment_v2, admin_user)
    live_from = timezone.now() + datetime.timedelta(hours=1)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=live_from,
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the pending change is surfaced as the scheduled change
    scheduled_change = _get_scheduled_change(document, feature.id)
    assert scheduled_change is not None
    assert scheduled_change["enabled"] is True
    assert scheduled_change["live_from"] == live_from


def test_scheduled_change__pending_change_set_not_opted_in__is_never_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given a committed change request with a pending VersionChangeSet
    _make_live_feature_state(environment_v2, feature, enabled=False)
    change_request = _committed_change_request(environment_v2, admin_user)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )

    # When mapped without opting in
    document = map_environment_to_sdk_document(environment_v2)

    # Then the key must be absent entirely, not present-and-null
    assert "scheduled_change" not in _get_feature_state(document, feature.id)


def test_scheduled_change__soft_deleted_change_request__is_not_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    """
    `change_request__...` in the pending-changeset query is a JOIN
    condition, not a query through ChangeRequest's own soft-delete manager
    — a soft-deleted (e.g. reverted) change request would still match
    unless excluded explicitly. Setting `deleted_at` via a queryset
    `.update()` isolates exactly that condition: calling the model's own
    `.delete()` would cascade the soft-delete onto the VersionChangeSet
    below too, which would then be excluded by its own manager regardless
    of this fix — that's not what's under test here.
    """
    # Given a committed but since soft-deleted change request with a
    # pending, not-yet-materialised VersionChangeSet
    _make_live_feature_state(environment_v2, feature, enabled=False)
    change_request = _committed_change_request(environment_v2, admin_user)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )
    ChangeRequest.objects.filter(id=change_request.id).update(deleted_at=timezone.now())

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then it is not surfaced as a scheduled change
    assert _get_scheduled_change(document, feature.id) is None


def test_scheduled_change__uncommitted_change_request__is_not_surfaced(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given a change request still in draft/review (never committed) — not a
    # locked-in change yet, and so must not be advertised to SDKs
    _make_live_feature_state(environment_v2, feature, enabled=False)
    change_request = ChangeRequest.objects.create(
        environment=environment_v2, title="draft change", user=admin_user
    )
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then it is not surfaced as a scheduled change
    assert _get_scheduled_change(document, feature.id) is None


def test_scheduled_change__pending_segment_override_update__is_surfaced(
    environment_v2: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
) -> None:
    """
    `feature_states_to_update` staged against an *existing* live segment
    override. `feature_states_to_create` (a brand new override with no
    live counterpart yet) is a known, separate gap: the mapper only ever
    attaches `scheduled_change` to an already-existing FeatureStateModel
    entry, and there is none to attach to until the override actually
    exists. Not covered here.
    """
    from features.models import FeatureSegment

    # Given an existing live segment override and a pending changeset update
    # to it
    live_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2,
        environment_feature_version=live_version,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2,
            environment_feature_version=live_version,
        ),
        enabled=False,
    )
    live_version.publish(admin_user)

    change_request = _committed_change_request(environment_v2, admin_user)
    live_from = timezone.now() + datetime.timedelta(hours=1)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=live_from,
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": {"segment": segment.id},
                    "feature": feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )

    # When mapped with include_scheduled opted in
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the pending update is surfaced on the segment override
    scheduled_change = _get_segment_scheduled_change(document, feature.id, segment.id)
    assert scheduled_change is not None
    assert scheduled_change["enabled"] is True
    assert scheduled_change["live_from"] == live_from


def test_scheduled_change__entry_missing_enabled__is_skipped(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    """
    The changeset JSON is `json.dumps()` of raw client input, only
    validated at publish time — and `enabled` is genuinely optional in
    the upstream create serializer (it has a model default), so an entry
    without it is a reachable at-rest shape. It must be skipped, not 500
    the document build for every opted-in client; other, well-formed
    changesets in the same environment must still surface.
    """
    # Given a changeset entry missing the "enabled" key, alongside a
    # well-formed changeset for another feature
    _make_live_feature_state(environment_v2, feature, enabled=False)
    other_feature = Feature.objects.create(
        name="well_formed_feature", project=environment_v2.project
    )
    change_request = _committed_change_request(environment_v2, admin_user)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": feature.id,
                    # no "enabled" key
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )
    live_from = timezone.now() + datetime.timedelta(hours=2)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=other_feature,
        change_request=change_request,
        live_from=live_from,
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": other_feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )

    # When mapped — must not raise
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the malformed entry is skipped...
    assert _get_scheduled_change(document, feature.id) is None
    # ...while the rest of the document — the live feature state and the
    # well-formed changeset for the other feature — is unaffected
    assert _get_feature_state(document, feature.id)["enabled"] is False
    other_scheduled = _get_scheduled_change(document, other_feature.id)
    assert other_scheduled is not None
    assert other_scheduled["enabled"] is True
    assert other_scheduled["live_from"] == live_from


def test_scheduled_change__non_dict_feature_segment_and_entry__are_skipped(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given a changeset with a non-dict `feature_segment` and a non-dict
    # entry
    _make_live_feature_state(environment_v2, feature, enabled=False)
    change_request = _committed_change_request(environment_v2, admin_user)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    # not an object — the mapper subscripts ["segment"]
                    "feature_segment": 42,
                    "feature": feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                },
                # not even an object at the entry level
                "nonsense",
            ]
        ),
    )

    # When mapped — must not raise
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then both malformed entries are skipped and the document is intact
    assert _get_scheduled_change(document, feature.id) is None
    assert _get_feature_state(document, feature.id)["enabled"] is False


def test_scheduled_change__non_list_changeset_json__is_skipped(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    """
    Even the top-level JSON shape is untrusted: a blob that isn't a list
    at all (on either field) must only disable *this* changeset's
    contribution — the rest of the environment document, including a
    well-formed changeset for another feature, must still build.
    """
    # Given a changeset whose top-level JSON isn't a list at all, alongside
    # a well-formed changeset for another feature
    _make_live_feature_state(environment_v2, feature, enabled=False)
    other_feature = Feature.objects.create(
        name="well_formed_feature", project=environment_v2.project
    )
    change_request = _committed_change_request(environment_v2, admin_user)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + datetime.timedelta(hours=1),
        feature_states_to_update=json.dumps({"not": "a list"}),
        feature_states_to_create=json.dumps("garbage"),
    )
    live_from = timezone.now() + datetime.timedelta(hours=2)
    VersionChangeSet.objects.create(
        environment=environment_v2,
        feature=other_feature,
        change_request=change_request,
        live_from=live_from,
        feature_states_to_update=json.dumps(
            [
                {
                    "environment": environment_v2.id,
                    "identity": None,
                    "feature_segment": None,
                    "feature": other_feature.id,
                    "enabled": True,
                    "feature_state_value": _bool_value(True),
                    "multivariate_feature_state_values": [],
                }
            ]
        ),
    )

    # When mapped — must not raise
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then the garbage changeset surfaces nothing for its feature...
    assert _get_scheduled_change(document, feature.id) is None
    # ...and the well-formed changeset for the other feature still does
    other_scheduled = _get_scheduled_change(document, other_feature.id)
    assert other_scheduled is not None
    assert other_scheduled["enabled"] is True
    assert other_scheduled["live_from"] == live_from


# -- Earliest-wins across both mechanisms -------------------------------------
# When BOTH mechanisms hold a pending change for the same feature — a future
# FeatureState that already exists in the DB (mechanism 1) and a
# committed-but-unpublished VersionChangeSet diff (mechanism 2) — the
# surfaced `scheduled_change` must be whichever goes live first, mirroring the
# earliest-wins rule each mechanism already applies internally
# (`map_feature_state_to_engine` compares the two candidates' `live_from` and
# keeps the earlier one). The two changes disagree on `enabled` so the
# assertions can tell which mechanism won.


def test_scheduled_change__earlier_feature_state_vs_later_change_set__feature_state_wins(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given the FeatureState-based change goes live an hour before the
    # changeset-based one
    _make_live_feature_state(environment_v2, feature, enabled=False)
    feature_state_live_from = timezone.now() + datetime.timedelta(hours=1)
    _make_future_feature_state(
        environment_v2, feature, enabled=True, live_from=feature_state_live_from
    )
    _pending_change_set(
        environment_v2,
        feature,
        admin_user,
        live_from=timezone.now() + datetime.timedelta(hours=2),
        enabled=False,
    )

    # When
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then — mechanism 1 (the future FeatureState) wins
    scheduled_change = _get_scheduled_change(document, feature.id)
    assert scheduled_change is not None
    assert scheduled_change["enabled"] is True
    assert scheduled_change["live_from"] == feature_state_live_from


def test_scheduled_change__earlier_change_set_vs_later_feature_state__change_set_wins(
    environment_v2: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given — the same setup with the timestamps swapped
    _make_live_feature_state(environment_v2, feature, enabled=False)
    change_set_live_from = timezone.now() + datetime.timedelta(hours=1)
    _make_future_feature_state(
        environment_v2,
        feature,
        enabled=True,
        live_from=timezone.now() + datetime.timedelta(hours=2),
    )
    _pending_change_set(
        environment_v2,
        feature,
        admin_user,
        live_from=change_set_live_from,
        enabled=False,
    )

    # When
    document = map_environment_to_sdk_document(environment_v2, include_scheduled=True)

    # Then — mechanism 2 (the pending changeset) wins
    scheduled_change = _get_scheduled_change(document, feature.id)
    assert scheduled_change is not None
    assert scheduled_change["enabled"] is False
    assert scheduled_change["live_from"] == change_set_live_from
