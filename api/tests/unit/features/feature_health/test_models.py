import datetime

from freezegun import freeze_time

from features.feature_health.models import FeatureHealthEvent
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project

now = datetime.datetime.now()


def test_feature_health_event__get_latest_by_feature__return_expected(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    unrelated_feature = Feature.objects.create(
        project=project, name="unrelated_feature"
    )

    latest_provider1_event = FeatureHealthEvent.objects.create(
        feature=feature,
        type="UNHEALTHY",
        provider_name="provider1",
    )
    with freeze_time(now - datetime.timedelta(hours=1)):
        older_provider1_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="HEALTHY",
            provider_name="provider1",
        )
    with freeze_time(now - datetime.timedelta(hours=2)):
        latest_provider2_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="UNHEALTHY",
            provider_name="provider2",
        )
    unrelated_feature_event = FeatureHealthEvent.objects.create(
        feature=unrelated_feature,
        type="UNHEALTHY",
        provider_name="provider1",
    )

    # When
    feature_health_events = [*FeatureHealthEvent.objects.get_latest_by_feature(feature)]

    # Then
    assert feature_health_events == [latest_provider1_event, latest_provider2_event]
    assert older_provider1_event not in feature_health_events
    assert unrelated_feature_event not in feature_health_events


def test_feature_health_event__get_latest_by_project__return_expected(
    project: Project,
    feature: Feature,
    organisation: Organisation,
) -> None:
    # Given
    another_feature = Feature.objects.create(project=project, name="another_feature")
    unrelated_project = Project.objects.create(
        organisation=organisation, name="unrelated_project"
    )
    unrelated_feature = Feature.objects.create(
        project=unrelated_project, name="unrelated_feature"
    )

    latest_provider1_event = FeatureHealthEvent.objects.create(
        feature=feature,
        type="UNHEALTHY",
        provider_name="provider1",
    )
    with freeze_time(now - datetime.timedelta(hours=1)):
        older_provider1_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="HEALTHY",
            provider_name="provider1",
        )
    with freeze_time(now - datetime.timedelta(hours=2)):
        latest_provider2_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="UNHEALTHY",
            provider_name="provider2",
        )
    with freeze_time(now - datetime.timedelta(hours=3)):
        another_feature_event = FeatureHealthEvent.objects.create(
            feature=another_feature,
            type="UNHEALTHY",
            provider_name="provider1",
        )
    unrelated_feature_event = FeatureHealthEvent.objects.create(
        feature=unrelated_feature,
        type="UNHEALTHY",
        provider_name="provider1",
    )

    # When
    feature_health_events = [*FeatureHealthEvent.objects.get_latest_by_project(project)]

    # Then
    assert feature_health_events == [
        latest_provider1_event,
        another_feature_event,
        latest_provider2_event,
    ]
    assert older_provider1_event not in feature_health_events
    assert unrelated_feature_event not in feature_health_events
