import pytest
from django.http import HttpRequest
from django.test import RequestFactory
from pytest_mock import MockerFixture

from features.feature_health.admin import FeatureHealthProviderAdmin
from features.feature_health.models import FeatureHealthProvider
from users.models import FFAdminUser


@pytest.fixture
def feature_health_provider_admin_request(
    admin_user: FFAdminUser,
    rf: RequestFactory,
) -> HttpRequest:
    request = rf.get("/admin/features/feature_health/featurehealthprovider/")
    request.user = admin_user
    return request


def test_feature_health_provider_admin__changelist_view__expected_request_set(
    feature_health_provider_admin_request: HttpRequest,
    mocker: MockerFixture,
) -> None:
    # Given
    admin_instance = FeatureHealthProviderAdmin(
        FeatureHealthProvider, mocker.MagicMock()
    )

    # When
    admin_instance.changelist_view(feature_health_provider_admin_request)

    # Then
    assert admin_instance.request == feature_health_provider_admin_request


def test_feature_health_provider_admin__webhook_url__return_expected(
    feature_health_provider_admin_request: HttpRequest,
    mocker: MockerFixture,
) -> None:
    # Given
    get_webhook_path_from_provider_mock = mocker.patch(
        "features.feature_health.admin.get_webhook_path_from_provider"
    )
    get_webhook_path_from_provider_mock.return_value = (
        "/api/v1/feature-health/"
        "IjgxZjU1OTU3NjJiMjRlYzNiMmIyY2QzYjA0NzM1YTljIg/OgsuQAL_3ZtIJEoS_L8W0B2Kb1f_1b70wY7IGWOakcs"
    )
    admin_instance = FeatureHealthProviderAdmin(
        FeatureHealthProvider, mocker.MagicMock()
    )
    feature_health_provider = FeatureHealthProvider(name="Sample")
    admin_instance.changelist_view(feature_health_provider_admin_request)

    # When
    webhook_url = admin_instance.webhook_url(feature_health_provider)

    # Then
    get_webhook_path_from_provider_mock.assert_called_once_with(feature_health_provider)
    assert (
        webhook_url == "http://testserver/api/v1/feature-health/"
        "IjgxZjU1OTU3NjJiMjRlYzNiMmIyY2QzYjA0NzM1YTljIg/OgsuQAL_3ZtIJEoS_L8W0B2Kb1f_1b70wY7IGWOakcs"
    )
