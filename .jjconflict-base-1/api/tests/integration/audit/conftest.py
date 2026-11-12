import pytest
from pytest_mock import MockerFixture

from organisations.subscriptions.metadata import BaseSubscriptionMetadata


@pytest.fixture(autouse=True)
def _subscription_metadata(mocker: MockerFixture) -> None:
    """Lift the free plan's audit log visibility limit, which hides all past logs."""
    mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        return_value=BaseSubscriptionMetadata(audit_log_visibility_days=None),
    )
