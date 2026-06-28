from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from api_keys.models import MasterAPIKey
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.tasks import trigger_feature_state_change_webhooks
from features.workflows.core.models import ChangeRequest
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType


@pytest.mark.parametrize(
    "user, api_key, changed_by",
    [
        (lazy_fixture("admin_user"), None, lazy_fixture("admin_user_email")),
        (
            None,
            lazy_fixture("master_api_key_object"),
            lazy_fixture("master_api_key_name"),
        ),
    ],
)
@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__value_updated__calls_webhooks_with_correct_data(
    mocker: MockerFixture,
    user: FFAdminUser | None,
    api_key: MasterAPIKey | None,
    changed_by: str,
) -> None:
    # Given
    initial_value = "initial"
    new_value = "new"

    organisation = Organisation.objects.create(name="Test organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    environment = Environment.objects.create(name="Test environment", project=project)
    feature = Feature.objects.create(
        name="Test feature", project=project, initial_value=initial_value
    )
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # Set user/master_api_key
    mocked_historical_record = mocker.patch("core.signals.HistoricalRecords")
    mocked_historical_record.thread.request.user.key = api_key
    feature_state._history_user = user

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    assert environment_webhook_call_args[0] == environment.id
    assert organisation_webhook_call_args[0] == organisation.id

    # verify that the data for both calls is the same
    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"]["feature_state_value"] == new_value
    assert data["previous_state"]["feature_state_value"] == initial_value
    assert data["changed_by"] == changed_by
    assert event_type == WebhookEventType.FLAG_UPDATED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__environment_default_created__sends_created_event(
    mocker: MockerFixture,
    organisation: Organisation,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    feature = Feature.objects.create(name="Created feature", project=project)
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    assert environment_webhook_call_args[0] == environment.id
    assert organisation_webhook_call_args[0] == organisation.id

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"]["feature"]["id"] == feature.id
    assert "previous_state" not in data
    assert event_type == WebhookEventType.FLAG_CREATED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__environment_created_for_existing_feature__sends_updated_event(
    mocker: MockerFixture,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    environment = Environment.objects.create(name="Created environment", project=project)
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]
    assert environment_webhook_call_args[2] == WebhookEventType.FLAG_UPDATED.value


@pytest.mark.parametrize("scheduled", [False, True])
@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__change_request_environment_default_created__sends_updated_event(
    mocker: MockerFixture,
    feature: Feature,
    environment: Environment,
    change_request: ChangeRequest,
    scheduled: bool,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        enabled=True,
        live_from=timezone.now() + timedelta(days=1) if scheduled else timezone.now(),
        change_request=change_request,
        version=None,
    )

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]
    assert environment_webhook_call_args[2] == WebhookEventType.FLAG_UPDATED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__segment_override_created__sends_updated_event(
    mocker: MockerFixture,
    feature: Feature,
    environment: Environment,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    env_default = FeatureState.objects.get(
        feature=feature, environment=environment, feature_segment__isnull=True
    )
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=not env_default.enabled,
    )

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]
    assert environment_webhook_call_args[2] == WebhookEventType.FLAG_UPDATED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__flag_deleted__sends_delete_event(  # type: ignore[no-untyped-def]
    mocker, organisation, project, environment, feature
):
    # Given
    new_value = "new"
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state, WebhookEventType.FLAG_DELETED)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    # verify that the data for both calls is the same
    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"] is None
    assert data["previous_state"]["feature_state_value"] == new_value
    assert event_type == WebhookEventType.FLAG_DELETED.value


@pytest.mark.django_db
def test_trigger_feature_state_change_webhooks__deleted_flag_no_history__uses_fs_instance(  # type: ignore[no-untyped-def]
    mocker: MockerFixture,
    environment: Environment,
    feature: Feature,
):
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # Remove history instance to make sure it's not used
    feature_state.history.all().delete()

    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mock_call_organisation_webhooks = mocker.patch(
        "features.tasks.call_organisation_webhooks"
    )

    # When
    trigger_feature_state_change_webhooks(feature_state, WebhookEventType.FLAG_DELETED)

    # Then
    environment_webhook_call_args = (
        mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    )
    organisation_webhook_call_args = (
        mock_call_organisation_webhooks.delay.call_args.kwargs["args"]
    )

    # verify that the data for both calls is the same
    assert environment_webhook_call_args[1] == organisation_webhook_call_args[1]

    data = environment_webhook_call_args[1]
    event_type = environment_webhook_call_args[2]
    assert data["new_state"] is None

    assert data["previous_state"]["feature"]["id"] == feature_state.feature.id
    assert event_type == WebhookEventType.FLAG_DELETED.value
