import datetime

from freezegun import freeze_time
from pytest_mock import MockerFixture

from environments.models import Environment
from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthProvider,
)
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser

now = datetime.datetime.now()


def test_feature_health_provider__get_create_log_message__return_expected(
    feature_health_provider: FeatureHealthProvider,
    mocker: MockerFixture,
) -> None:
    # When
    log_message = feature_health_provider.get_create_log_message(mocker.Mock())

    # Then
    assert log_message == "Health provider Sample set up for project Test Project."


def test_feature_health_provider__get_delete_log_message__return_expected(
    feature_health_provider: FeatureHealthProvider,
    mocker: MockerFixture,
) -> None:
    # When
    log_message = feature_health_provider.get_delete_log_message(mocker.Mock())

    # Then
    assert log_message == "Health provider Sample removed from project Test Project."


def test_feature_health_provider__get_audit_log_author__return_expected(
    feature_health_provider: FeatureHealthProvider,
    mocker: MockerFixture,
    staff_user: FFAdminUser,
) -> None:
    # When
    audit_log_author = feature_health_provider.get_audit_log_author(mocker.Mock())

    # Then
    assert audit_log_author == staff_user


def test_feature_health_event__get_latest_by_feature__return_expected(
    project: Project,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    unrelated_feature = Feature.objects.create(
        project=project, name="unrelated_feature"
    )
    environment_2 = Environment.objects.create(project=project, name="Environment 2")

    latest_provider1_event = FeatureHealthEvent.objects.create(
        feature=feature,
        type="UNHEALTHY",
        provider_name="provider1",
    )
    latest_provider1_environment_event = FeatureHealthEvent.objects.create(
        feature=feature,
        type="UNHEALTHY",
        provider_name="provider1",
        environment=environment,
    )
    with freeze_time(now - datetime.timedelta(hours=1)):
        older_provider1_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="HEALTHY",
            provider_name="provider1",
        )
        older_provider1_environment_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="HEALTHY",
            provider_name="provider1",
            environment=environment,
        )
        latest_provider_1_environment_2_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="UNHEALTHY",
            provider_name="provider1",
            environment=environment_2,
        )
    with freeze_time(now - datetime.timedelta(hours=2)):
        latest_provider2_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="UNHEALTHY",
            provider_name="provider2",
        )
        older_provider_1_environment_2_event = FeatureHealthEvent.objects.create(
            feature=feature,
            type="HEALTHY",
            provider_name="provider1",
            environment=environment_2,
        )
    unrelated_feature_event = FeatureHealthEvent.objects.create(
        feature=unrelated_feature,
        type="UNHEALTHY",
        provider_name="provider1",
    )

    # When
    feature_health_events = [*FeatureHealthEvent.objects.get_latest_by_feature(feature)]

    # Then
    assert feature_health_events == [
        latest_provider1_environment_event,
        latest_provider_1_environment_2_event,
        latest_provider1_event,
        latest_provider2_event,
    ]
    assert older_provider1_event not in feature_health_events
    assert older_provider1_environment_event not in feature_health_events
    assert older_provider_1_environment_2_event not in feature_health_events
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


def test_feature_health_event__get_create_log_message__return_expected(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    feature_health_event = FeatureHealthEvent.objects.create(
        feature=feature,
        type="UNHEALTHY",
        provider_name="provider1",
        reason="Test reason",
    )

    # When
    log_message = feature_health_event.get_create_log_message(mocker.Mock())

    # Then
    assert (
        log_message == "Health status changed to UNHEALTHY for feature Test Feature1."
        "\n\nProvided by provider1\n\nReason:\nTest reason"
    )


def test_feature_health_event__get_create_log_message__environment__return_expected(
    feature: Feature,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    feature_health_event = FeatureHealthEvent.objects.create(
        feature=feature,
        environment=environment,
        type="UNHEALTHY",
    )

    # When
    log_message = feature_health_event.get_create_log_message(mocker.Mock())

    # Then
    assert (
        log_message
        == "Health status changed to UNHEALTHY for feature Test Feature1 in environment Test Environment."
    )
