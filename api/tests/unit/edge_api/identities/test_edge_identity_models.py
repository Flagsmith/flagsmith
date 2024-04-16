from datetime import timedelta
from unittest.mock import MagicMock

import pytest
import shortuuid
from django.utils import timezone
from flag_engine.features.models import FeatureModel, FeatureStateModel
from freezegun import freeze_time
from pytest_mock import MockerFixture

from edge_api.identities.models import EdgeIdentity
from features.models import FeatureSegment, FeatureState, FeatureStateValue
from features.workflows.core.models import ChangeRequest
from segments.models import Segment


def test_get_all_feature_states_for_edge_identity_uses_segment_priorities(
    environment, project, segment, feature, mocker
):
    # Given
    another_segment = Segment.objects.create(name="another_segment", project=project)

    edge_identity_dynamo_wrapper_mock = mocker.patch(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper",
    )
    edge_identity_dynamo_wrapper_mock.get_segment_ids.return_value = [
        segment.id,
        another_segment.id,
    ]

    feature_segment_p1 = FeatureSegment.objects.create(
        segment=segment, feature=feature, environment=environment, priority=1
    )
    feature_segment_p2 = FeatureSegment.objects.create(
        segment=another_segment, feature=feature, environment=environment, priority=2
    )

    segment_override_p1 = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment_p1
    )
    segment_override_p2 = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment_p2
    )

    FeatureStateValue.objects.filter(feature_state=segment_override_p1).update(
        string_value="p1"
    )
    FeatureStateValue.objects.filter(feature_state=segment_override_p2).update(
        string_value="p2"
    )

    identity_model = mocker.MagicMock(
        environment_api_key=environment.api_key, identity_features=[]
    )
    edge_identity = EdgeIdentity(identity_model)

    # When
    feature_states, _ = edge_identity.get_all_feature_states()

    # Then
    assert len(feature_states) == 1
    assert feature_states[0] == segment_override_p1

    edge_identity_dynamo_wrapper_mock.get_segment_ids.assert_called_once_with(
        identity_model=identity_model
    )


def test_edge_identity_get_all_feature_states_ignores_not_live_feature_states(
    environment, project, segment, feature, feature_state, admin_user, mocker
):
    # Given
    edge_identity_dynamo_wrapper_mock = mocker.patch(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper",
    )
    edge_identity_dynamo_wrapper_mock.get_segment_ids.return_value = []

    change_request = ChangeRequest.objects.create(
        title="Test CR", environment=environment, user=admin_user
    )
    FeatureState.objects.create(
        version=None,
        live_from=feature_state.live_from + timedelta(hours=1),
        feature=feature,
        environment=environment,
        change_request=change_request,
    )

    identity_model = mocker.MagicMock(
        environment_api_key=environment.api_key, identity_features=[]
    )
    edge_identity = EdgeIdentity(identity_model)

    # When
    with freeze_time(timezone.now() + timedelta(hours=2)):
        feature_states, _ = edge_identity.get_all_feature_states()

    # Then
    assert feature_states == [feature_state]


def test_edge_identity_from_identity_document():
    # Given
    identifier = "identifier"
    environment_api_key = shortuuid.uuid()

    # When
    edge_identity = EdgeIdentity.from_identity_document(
        {"identifier": identifier, "environment_api_key": environment_api_key}
    )

    # Then
    assert edge_identity.identifier == identifier
    assert edge_identity.identity_uuid
    assert edge_identity.environment_api_key == environment_api_key


@pytest.mark.parametrize(
    "django_id, identity_uuid, expected_id",
    (
        (1, "a35a02f2-fefd-4932-8f5c-e84a0bf542c7", 1),
        (
            None,
            "a35a02f2-fefd-4932-8f5c-e84a0bf542c7",
            "a35a02f2-fefd-4932-8f5c-e84a0bf542c7",
        ),
    ),
)
def test_edge_identity_id_property(django_id, identity_uuid, expected_id, mocker):
    # When
    edge_identity = EdgeIdentity(
        mocker.MagicMock(django_id=django_id, identity_uuid=identity_uuid)
    )

    # Then
    assert edge_identity.id == expected_id


def test_edge_identity_get_feature_state_by_feature_name_or_id(edge_identity_model):
    # Given
    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )
    edge_identity_model.add_feature_override(feature_state_model)

    # When
    found_by_name = edge_identity_model.get_feature_state_by_feature_name_or_id(
        feature_state_model.feature.name
    )
    found_by_id = edge_identity_model.get_feature_state_by_feature_name_or_id(
        feature_state_model.feature.id
    )

    # Then
    assert found_by_name == found_by_id == feature_state_model
    assert (
        edge_identity_model.get_feature_state_by_feature_name_or_id("invalid") is None
    )


def test_edge_identity_get_feature_state_by_featurestate_uuid(edge_identity_model):
    # Given
    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )
    edge_identity_model.add_feature_override(feature_state_model)

    # When
    found_by_feature_state_uuid = (
        edge_identity_model.get_feature_state_by_featurestate_uuid(
            str(feature_state_model.featurestate_uuid)
        )
    )

    # Then
    assert found_by_feature_state_uuid == feature_state_model
    assert edge_identity_model.get_feature_state_by_featurestate_uuid("invalid") is None


def test_edge_identity_remove_feature_state(edge_identity_model):
    # Given
    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )
    edge_identity_model.add_feature_override(feature_state_model)

    # When
    edge_identity_model.remove_feature_override(feature_state_model)

    # Then
    assert (
        edge_identity_model.get_feature_state_by_feature_name_or_id(
            feature_state_model.feature.id
        )
        is None
    )


def test_edge_identity_remove_feature_state_if_no_matching_feature_state(
    edge_identity_model,
):
    # Given
    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )

    # When
    edge_identity_model.remove_feature_override(feature_state_model)

    # Then
    assert (
        edge_identity_model.get_feature_state_by_feature_name_or_id(
            feature_state_model.feature.id
        )
        is None
    )


def test_edge_identity_synchronise_features(mocker, edge_identity_model):
    # Given
    mock_sync_identity_document_features = mocker.patch(
        "edge_api.identities.models.sync_identity_document_features"
    )

    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )
    edge_identity_model.add_feature_override(feature_state_model)

    # When
    edge_identity_model.synchronise_features([])

    # Then
    assert (
        edge_identity_model.get_feature_state_by_feature_name_or_id(
            feature_state_model.feature.id
        )
        is None
    )
    mock_sync_identity_document_features.delay.assert_called_once_with(
        args=(str(edge_identity_model.identity_uuid),)
    )


def test_edge_identity_save_does_not_generate_audit_records_if_no_changes(
    mocker, edge_identity_model, edge_identity_dynamo_wrapper_mock
):
    # Given
    mocked_generate_audit_log_records = mocker.patch(
        "edge_api.identities.models.generate_audit_log_records"
    )

    user = mocker.MagicMock()

    # When
    edge_identity_model.save(user=user)

    # Then
    edge_identity_dynamo_wrapper_mock.put_item.assert_called_once()
    mocked_generate_audit_log_records.delay.assert_not_called()


def test_edge_identity_save_called__feature_override_added__expected_tasks_called(
    mocker: MockerFixture,
    edge_identity_model: EdgeIdentity,
    edge_identity_dynamo_wrapper_mock: MagicMock,
) -> None:
    # Given
    mocked_generate_audit_log_records = mocker.patch(
        "edge_api.identities.models.generate_audit_log_records"
    )
    mocked_update_flagsmith_environments_v2_identity_overrides = mocker.patch(
        "edge_api.identities.models.update_flagsmith_environments_v2_identity_overrides"
    )

    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )
    edge_identity_model.add_feature_override(feature_state_model)

    user = mocker.MagicMock()

    expected_changes = {
        "feature_overrides": {
            "test_feature": {
                "change_type": "+",
                "new": {
                    **feature_state_model.dict(),
                    "enabled": True,
                    "feature_state_value": None,
                },
            }
        }
    }
    expected_identity_uuid = str(edge_identity_model.identity_uuid)

    # When
    edge_identity_model.save(user=user)

    # Then
    edge_identity_dynamo_wrapper_mock.put_item.assert_called_once()
    mocked_generate_audit_log_records.delay.assert_called_once_with(
        kwargs={
            "environment_api_key": edge_identity_model.environment_api_key,
            "identifier": edge_identity_model.identifier,
            "user_id": user.id,
            "changes": expected_changes,
            "identity_uuid": expected_identity_uuid,
            "master_api_key_id": None,
        }
    )
    mocked_update_flagsmith_environments_v2_identity_overrides.delay.assert_called_once_with(
        kwargs={
            "environment_api_key": edge_identity_model.environment_api_key,
            "changes": expected_changes,
            "identity_uuid": expected_identity_uuid,
            "identifier": edge_identity_model.identifier,
        }
    )


def test_edge_identity_save_called__feature_override_removed__expected_tasks_called(
    mocker: MockerFixture,
    edge_identity_model: EdgeIdentity,
    edge_identity_dynamo_wrapper_mock: MagicMock,
) -> None:
    # Given
    mocked_generate_audit_log_records = mocker.patch(
        "edge_api.identities.models.generate_audit_log_records"
    )
    mocked_update_flagsmith_environments_v2_identity_overrides = mocker.patch(
        "edge_api.identities.models.update_flagsmith_environments_v2_identity_overrides"
    )

    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=True,
    )
    edge_identity_model.add_feature_override(feature_state_model)

    user = mocker.MagicMock()

    expected_changes = {
        "feature_overrides": {
            "test_feature": {
                "change_type": "-",
                "old": {
                    **feature_state_model.dict(),
                    "enabled": True,
                    "feature_state_value": None,
                },
            }
        }
    }
    expected_identity_uuid = str(edge_identity_model.identity_uuid)

    edge_identity_model.save(user=user)
    edge_identity_dynamo_wrapper_mock.reset_mock()
    mocked_generate_audit_log_records.reset_mock()
    mocked_update_flagsmith_environments_v2_identity_overrides.reset_mock()

    edge_identity_model.remove_feature_override(feature_state_model)

    # When
    edge_identity_model.save(user=user)

    # Then
    edge_identity_dynamo_wrapper_mock.put_item.assert_called_once()
    mocked_generate_audit_log_records.delay.assert_called_once_with(
        kwargs={
            "environment_api_key": edge_identity_model.environment_api_key,
            "identifier": edge_identity_model.identifier,
            "user_id": user.id,
            "changes": expected_changes,
            "identity_uuid": expected_identity_uuid,
            "master_api_key_id": None,
        }
    )
    mocked_update_flagsmith_environments_v2_identity_overrides.delay.assert_called_once_with(
        kwargs={
            "environment_api_key": edge_identity_model.environment_api_key,
            "changes": expected_changes,
            "identity_uuid": expected_identity_uuid,
            "identifier": edge_identity_model.identifier,
        }
    )


@pytest.mark.parametrize(
    "initial_enabled, initial_value, new_enabled, new_value",
    (
        (True, "initial", True, "updated"),
        (False, "initial", True, "initial"),
        (False, "initial", True, "updated"),
    ),
)
def test_edge_identity_save_called_generate_audit_records_if_feature_override_updated(
    initial_enabled: bool,
    initial_value: str,
    new_enabled: bool,
    new_value: str,
    mocker: MockerFixture,
    edge_identity_model: EdgeIdentity,
    edge_identity_dynamo_wrapper_mock: MagicMock,
) -> None:
    # Given
    mocked_generate_audit_log_records = mocker.patch(
        "edge_api.identities.models.generate_audit_log_records"
    )
    mocked_update_flagsmith_environments_v2_identity_overrides = mocker.patch(
        "edge_api.identities.models.update_flagsmith_environments_v2_identity_overrides"
    )

    feature_state_model = FeatureStateModel(
        feature=FeatureModel(id=1, name="test_feature", type="STANDARD"),
        enabled=initial_enabled,
    )
    feature_state_model.set_value(initial_value)
    edge_identity_model.add_feature_override(feature_state_model)

    user = mocker.MagicMock()

    expected_changes = {
        "feature_overrides": {
            "test_feature": {
                "change_type": "~",
                "old": {
                    **feature_state_model.dict(),
                    "enabled": initial_enabled,
                    "feature_state_value": initial_value,
                },
                "new": {
                    **feature_state_model.dict(),
                    "enabled": new_enabled,
                    "feature_state_value": new_value,
                },
            }
        }
    }
    expected_identity_uuid = str(edge_identity_model.identity_uuid)

    edge_identity_model.save(user=user)
    edge_identity_dynamo_wrapper_mock.reset_mock()
    mocked_generate_audit_log_records.reset_mock()
    mocked_update_flagsmith_environments_v2_identity_overrides.reset_mock()

    feature_override = edge_identity_model.get_feature_state_by_featurestate_uuid(
        str(feature_state_model.featurestate_uuid)
    )
    feature_override.enabled = new_enabled
    feature_override.set_value(new_value)

    # When
    edge_identity_model.save(user=user)

    # Then
    edge_identity_dynamo_wrapper_mock.put_item.assert_called_once()
    mocked_generate_audit_log_records.delay.assert_called_once_with(
        kwargs={
            "environment_api_key": edge_identity_model.environment_api_key,
            "identifier": edge_identity_model.identifier,
            "user_id": user.id,
            "changes": expected_changes,
            "identity_uuid": expected_identity_uuid,
            "master_api_key_id": None,
        }
    )
    mocked_update_flagsmith_environments_v2_identity_overrides.delay.assert_called_once_with(
        kwargs={
            "environment_api_key": edge_identity_model.environment_api_key,
            "changes": expected_changes,
            "identity_uuid": expected_identity_uuid,
            "identifier": edge_identity_model.identifier,
        }
    )
