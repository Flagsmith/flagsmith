from app_analytics.views import SDKAnalyticsFlags
from rest_framework import status


def test_sdk_analytics_does_not_allow_bad_data(mocker, settings, environment):
    # Given
    settings.INFLUXDB_TOKEN = "some-token"

    data = {"bad": "data"}
    request = mocker.MagicMock(data=data, environment=environment)

    view = SDKAnalyticsFlags(request=request)

    mocked_track_feature_eval = mocker.patch(
        "app_analytics.views.track_feature_evaluation_influxdb"
    )

    # When
    response = view.post(request)

    # Then
    assert response.status_code == status.HTTP_200_OK
    mocked_track_feature_eval.assert_not_called()


def test_sdk_analytics_allows_valid_data(mocker, settings, environment, feature):
    # Given
    settings.INFLUXDB_TOKEN = "some-token"

    data = {feature.name: 12}
    request = mocker.MagicMock(data=data, environment=environment)

    view = SDKAnalyticsFlags(request=request)

    mocked_track_feature_eval = mocker.patch(
        "app_analytics.views.track_feature_evaluation_influxdb"
    )

    # When
    response = view.post(request)

    # Then
    assert response.status_code == status.HTTP_200_OK
    mocked_track_feature_eval.assert_called_once_with(environment.id, data)
