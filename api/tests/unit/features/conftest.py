import pytest
from pytest_mock import MockerFixture

from features.models import FeatureState
from users.models import FFAdminUser


@pytest.fixture()
def feature_state_version_generator(environment, feature, request):  # type: ignore[no-untyped-def]
    version_1 = request.param[0]
    version_1_live_from = request.param[1]
    version_2 = request.param[2]
    version_2_live_from = request.param[3]
    expected_result = request.param[4]

    return (
        FeatureState.objects.create(
            feature=feature,
            environment=environment,
            version=version_1,
            live_from=version_1_live_from,
        ),
        FeatureState.objects.create(
            feature=feature,
            environment=environment,
            version=version_2,
            live_from=version_2_live_from,
        ),
        expected_result,
    )


@pytest.fixture
def admin_history(
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    """
    Fixture to patch `simple_history` to set the user on historical records to an admin user.
    """

    historical_records_thread_mock = mocker.MagicMock()
    historical_records_thread_mock.request.user = admin_user

    mocker.patch(
        "simple_history.models.HistoricalRecords.thread",
        historical_records_thread_mock,
    )
