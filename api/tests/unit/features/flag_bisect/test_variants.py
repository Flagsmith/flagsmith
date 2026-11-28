import typing
from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper

from core.dataclasses import AuthorData
from environments.models import Environment
from features.flag_bisect import services
from features.flag_bisect.models import Incident, IncidentState, Suspect
from features.future.services import get_flag, update_flag
from features.future.types import Variant
from features.models import Feature
from segments.models import Segment
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def flag_bisect_enabled(settings: SettingsWrapper) -> None:
    settings.FLAG_BISECT_ENABLED = True


@pytest.fixture(params=["v1", "v2"])
def any_environment(
    request: pytest.FixtureRequest, environment: Environment
) -> Environment:
    if request.param == "v2":
        return typing.cast(
            Environment, request.getfixturevalue("environment_v2_versioning")
        )
    return environment


def test_apply__multivariate_suspect__canary_keeps_the_variant_split(
    any_environment: Environment,
    multivariate_feature: Feature,
    admin_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given a multivariate flag with this environment's own split, switched on
    environment = any_environment
    # The fixture created the flag at the real time; only move forward from it.
    freezer.tick(timedelta(seconds=1))
    options = list(multivariate_feature.multivariate_options.order_by("id"))
    custom: list[Variant] = [
        {"id": options[0].id, "weight": 10},
        {"id": options[1].id, "weight": 0},
        {"id": options[2].id, "weight": 90},
    ]
    update_flag(
        environment=environment,
        feature=multivariate_feature,
        changes={"environment_default": {"enabled": True, "variants": custom}},
        replace=False,
        author=AuthorData(user=admin_user),
        overwrite_system_segment_overrides=False,
    )
    split = get_flag(environment=environment, feature=multivariate_feature)[
        "environment_default"
    ]["variants"]
    canary = Segment.objects.create(name="canary", project=environment.project)
    incident = Incident.objects.create(
        environment=environment,
        state=IncidentState.PROBING,
        onset_at=timezone.now(),
        baseline_rate=0.01,
        regression_rate=0.09,
        envelope_approved_by=admin_user,
        envelope_approved_at=timezone.now(),
        canary_segment=canary,
    )
    suspect = Suspect.objects.create(
        incident=incident,
        feature=multivariate_feature,
        before_enabled=False,
        after_enabled=True,
        changed_at=timezone.now(),
    )

    # When the canary reverts it
    services._apply(incident, [suspect])

    # Then only the on/off state is reverted; identities keep the same split
    override = next(
        o
        for o in get_flag(environment=environment, feature=multivariate_feature)[
            "segment_overrides"
        ]
        if o["segment"]["id"] == canary.id
    )
    assert sorted((v["id"], v["weight"]) for v in split) == sorted(
        (v["id"], v["weight"]) for v in custom
    )
    assert override["enabled"] is False
    assert sorted((v["id"], v["weight"]) for v in override["variants"]) == sorted(
        (v["id"], v["weight"]) for v in split
    )
