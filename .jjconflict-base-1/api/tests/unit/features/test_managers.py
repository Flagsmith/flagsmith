from datetime import datetime, timedelta, timezone

import pytest
from freezegun.api import FrozenDateTimeFactory

from environments.models import Environment
from features.models import FeatureState


@pytest.mark.django_db
def test_get_live_feature_states__latest_state_superseded_by_earlier_scheduled_update__returns_scheduled_update(
    environment: Environment,
    feature_state: FeatureState,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    tomorrow_state = feature_state.clone(environment, live_from=tomorrow, version=2)
    today_state = feature_state.clone(
        environment, live_from=datetime.now(timezone.utc), version=3
    )

    # When
    live_today = FeatureState.objects.get_live_feature_states(environment=environment)
    freezer.move_to(tomorrow + timedelta(minutes=1))
    live_tomorrow = FeatureState.objects.get_live_feature_states(
        environment=environment
    )

    # Then
    assert list(live_today) == [today_state]
    assert list(live_tomorrow) == [tomorrow_state]
