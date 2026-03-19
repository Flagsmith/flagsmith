from datetime import timedelta
from unittest import mock

import freezegun
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from environments.identities.models import Identity
from environments.models import Environment
from features.constants import ENVIRONMENT, FEATURE_SEGMENT, IDENTITY
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.versioning.models import EnvironmentFeatureVersion
from features.workflows.core.models import ChangeRequest
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment
from users.models import FFAdminUser

now = timezone.now()
yesterday = now - timedelta(days=1)
tomorrow = now + timedelta(days=1)


def test_feature_create__multiple_environments__creates_feature_states_for_all(
    db: None,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    # When
    feature = Feature.objects.create(name="Test Feature", project=project)

    # Then
    feature_states = FeatureState.objects.filter(feature=feature)
    assert feature_states.count() == 2


def test_feature_save__update_existing_feature__does_not_change_feature_state_enabled(
    db: None,
    project: Project,
) -> None:
    # Given
    default_enabled = True
    feature = Feature.objects.create(
        name="Test Feature", project=project, default_enabled=default_enabled
    )

    # When
    # we update the default_enabled state of the feature and save it again
    feature.default_enabled = not default_enabled
    feature.save()

    # Then
    # we expect that the feature state enabled values have not changed
    assert all(fs.enabled == default_enabled for fs in feature.feature_states.all())


def test_feature_create__with_initial_value__sets_value_for_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    # When
    value = "This is a value"
    feature = Feature.objects.create(
        name="Test Feature", project=project, initial_value=value
    )

    # Then
    feature_states = FeatureState.objects.filter(feature=feature)

    assert feature_states.count() == 2
    for feature_state in feature_states:
        feature_state.get_feature_state_value() == value


def test_feature_create__with_integer_initial_value__sets_integer_value_for_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    initial_value = 1
    feature = Feature.objects.create(
        name="Test feature",
        project=project,
        initial_value=initial_value,
    )

    # When
    feature_states = FeatureState.objects.filter(feature=feature)

    # Then
    assert feature_states.count() == 2
    for feature_state in feature_states:
        assert feature_state.get_feature_state_value() == initial_value


def test_feature_create__with_boolean_initial_value__sets_boolean_value_for_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    initial_value = False
    feature = Feature.objects.create(
        name="Test feature",
        project=project,
        initial_value=initial_value,
    )

    # When
    feature_states = FeatureState.objects.filter(feature=feature)

    # Then
    assert feature_states.count() == 2
    for feature_state in feature_states:
        assert feature_state.get_feature_state_value() == initial_value


def test_feature_create__duplicate_case_insensitive_name__raises_integrity_error(
    project: Project,
) -> None:
    # Given
    feature_name = "Test Feature"

    feature_one = Feature(project=project, name=feature_name)
    feature_two = Feature(project=project, name=feature_name.lower())

    # When
    feature_one.save()

    # Then
    with pytest.raises(IntegrityError):
        feature_two.save()


def test_feature_save__update_name__updates_feature_states(
    project: Project,
) -> None:
    # Given
    old_feature_name = "old_feature"
    new_feature_name = "new_feature"

    feature = Feature.objects.create(project=project, name=old_feature_name)

    # When
    feature.name = new_feature_name
    feature.save()

    # Then
    FeatureState.objects.filter(feature__name=new_feature_name).exists()


def test_feature_full_clean__duplicate_case_insensitive_name__raises_validation_error(
    project: Project,
) -> None:
    # Given
    feature_name = "Test Feature"
    Feature.objects.create(name=feature_name, initial_value="test", project=project)

    # When / Then
    with pytest.raises(ValidationError):
        feature_two = Feature(
            name=feature_name.lower(),
            initial_value="test",
            project=project,
        )
        feature_two.full_clean()


def test_feature_full_clean__same_feature_case_insensitive_name__allows_update(
    project: Project,
) -> None:
    # Given
    feature_name = "Test Feature"
    feature = Feature.objects.create(
        project=project, name=feature_name, initial_value="test"
    )

    # When
    feature.name = feature_name.lower()

    # Then
    # Should not raise error as the same Object.
    feature.full_clean()


def test_feature_create__with_tags__succeeds(project: Project) -> None:
    # Given
    tag1 = Tag.objects.create(
        label="Test Tag 1",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    tag2 = Tag.objects.create(
        label="Test Tag 2",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    feature = Feature.objects.create(project=project, name="test feature")

    # When
    feature.tags.set([tag1, tag2])
    feature.save()

    # Then
    assert feature.tags.count() == 2
    assert list(feature.tags.all()) == [tag1, tag2]


def test_feature_state_save__duplicate_in_environment__raises_validation_error(
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    duplicate_feature_state = FeatureState(
        feature=feature, environment=environment, enabled=True
    )

    # When
    with pytest.raises(ValidationError):
        duplicate_feature_state.save()

    # Then
    assert (
        FeatureState.objects.filter(feature=feature, environment=environment).count()
        == 1
    )


def test_feature_state_save__duplicate_for_segment__raises_validation_error(
    project: Project,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    segment = Segment.objects.create(project=project)
    feature_segment = FeatureSegment.objects.create(
        feature=feature, environment=environment, segment=segment
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
    )

    duplicate_feature_state = FeatureState(
        feature=feature,
        environment=environment,
        enabled=True,
        feature_segment=feature_segment,
    )

    # When
    with pytest.raises(ValidationError):
        duplicate_feature_state.save()

    # Then
    assert (
        FeatureState.objects.filter(
            feature=feature,
            environment=environment,
            feature_segment=feature_segment,
        ).count()
        == 1
    )


def test_feature_state_save__duplicate_for_identity__raises_validation_error(
    project: Project,
    feature: Feature,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity
    )

    duplicate_feature_state = FeatureState(
        feature=feature,
        environment=environment,
        enabled=True,
        identity=identity,
    )

    # When
    with pytest.raises(ValidationError):
        duplicate_feature_state.save()

    # Then
    assert (
        FeatureState.objects.filter(
            feature=feature, environment=environment, identity=identity
        ).count()
        == 1
    )


def test_feature_state_gt__various_types__returns_correct_priority_order(
    identity: Identity,
    feature: Feature,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    segment_1 = Segment.objects.create(name="Test Segment 1", project=project)
    segment_2 = Segment.objects.create(name="Test Segment 2", project=project)
    feature_segment_p1 = FeatureSegment.objects.create(
        segment=segment_1,
        feature=feature,
        environment=environment,
        priority=1,
    )
    feature_segment_p2 = FeatureSegment.objects.create(
        segment=segment_2,
        feature=feature,
        environment=environment,
        priority=2,
    )

    # When
    identity_state = FeatureState.objects.create(
        identity=identity, feature=feature, environment=environment
    )

    segment_1_state = FeatureState.objects.create(
        feature_segment=feature_segment_p1,
        feature=feature,
        environment=environment,
    )
    segment_2_state = FeatureState.objects.create(
        feature_segment=feature_segment_p2,
        feature=feature,
        environment=environment,
    )
    default_env_state = FeatureState.objects.get(
        environment=environment, identity=None, feature_segment=None
    )

    # Then - identity state is higher priority than all
    assert identity_state > segment_1_state
    assert identity_state > segment_2_state
    assert identity_state > default_env_state

    # and feature state with feature segment with highest priority is greater than feature state with lower
    # priority feature segment and default environment state
    assert segment_1_state > segment_2_state
    assert segment_1_state > default_env_state

    # and feature state with any segment is greater than default environment state
    assert segment_2_state > default_env_state


def test_feature_state_gt__missing_environment_feature_version__raises_value_error(
    identity: Identity,
    feature: Feature,
    feature_state: FeatureState,
    environment: Environment,
    environment_v2_versioning: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    feature_state2 = FeatureState.objects.create(
        identity=identity, feature=feature, environment=environment
    )
    mocker.patch.object(
        FeatureState,
        "type",
        new_callable=mocker.PropertyMock,
        return_value="ENVIRONMENT",
    )

    # When
    with pytest.raises(ValueError) as exception:
        assert feature_state > feature_state2

    # Then
    assert (
        exception.value.args[0]
        == "Cannot compare feature states as they are missing environment_feature_version."
    )


def test_feature_state_gt__different_environments__raises_value_error(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    another_environment = Environment.objects.create(
        name="Another environment", project=project
    )
    feature_state_env_1 = FeatureState.objects.filter(environment=environment).first()
    feature_state_env_2 = FeatureState.objects.filter(
        environment=another_environment
    ).first()

    # When / Then - exception raised
    with pytest.raises(ValueError):
        feature_state_env_1 > feature_state_env_2


def test_feature_state_gt__different_features__raises_value_error(
    project: Project,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    another_feature = Feature.objects.create(name="Another feature", project=project)
    feature_state_env_1 = FeatureState.objects.filter(feature=feature).first()
    feature_state_env_2 = FeatureState.objects.filter(feature=another_feature).first()

    # When / Then - exception raised
    with pytest.raises(ValueError):
        feature_state_env_1 > feature_state_env_2


def test_feature_state_gt__different_identities__raises_value_error(
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    identity_1 = Identity.objects.create(
        identifier="identity_1", environment=environment
    )
    identity_2 = Identity.objects.create(
        identifier="identity_2", environment=environment
    )

    feature_state_identity_1 = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity_1
    )
    feature_state_identity_2 = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity_2
    )

    # When / Then - exception raised
    with pytest.raises(ValueError):
        feature_state_identity_1 > feature_state_identity_2


def test_feature_state_gt__environment_default__returns_expected(
    environment: Environment,
    feature: Feature,
    identity: Identity,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    feature_state_identity = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity
    )
    feature_state_segment = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
    )

    # When / Then
    assert not feature_state > feature_state_identity
    assert not feature_state > feature_state_segment


@pytest.mark.parametrize(
    "feature_identity, expected_result",
    [
        (
            lazy_fixture("identity"),
            "Identity test_identity - Project Test Project - Environment Test Environment - Feature Test Feature1 - Enabled: False",
        ),
        (
            None,
            "Project Test Project - Environment Test Environment - Feature Test Feature1 - Enabled: False",
        ),
    ],
)
def test_feature_state_str__with_or_without_identity__returns_expected(
    feature_state: FeatureState,
    feature_identity: Identity | None,
    expected_result: str,
) -> None:
    # Given
    feature_state.identity = feature_identity

    # When & Then
    assert str(feature_state) == expected_result


@mock.patch("features.tasks.trigger_feature_state_change_webhooks")
def test_feature_state_save__with_change__calls_trigger_webhooks(
    mock_trigger_webhooks: mock.MagicMock,
    feature: Feature,
    environment: Environment,
    admin_history: None,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    # Make an actual change so the webhook is triggered
    feature_state.enabled = not feature_state.enabled

    # When
    # Feature state saved with admin history thread context
    feature_state.save()

    # Then - Webhook is triggered via AuditLog signal chain
    mock_trigger_webhooks.assert_called_once()
    called_feature_state = mock_trigger_webhooks.call_args[0][0]
    assert called_feature_state.id == feature_state.id


def test_feature_delete__with_feature_states__does_not_trigger_webhooks(
    mocker: MockerFixture,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    mock_trigger_webhooks = mocker.patch(
        "features.tasks.trigger_feature_state_change_webhooks"
    )

    # When
    feature.delete()

    # Then
    mock_trigger_webhooks.assert_not_called()


def test_feature_state_type__environment_state__returns_environment(
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=feature,
        identity=None,
        feature_segment=None,
    )

    # When
    result = feature_state.type

    # Then
    assert result == ENVIRONMENT


def test_feature_state_type__identity_state__returns_identity(
    identity: Identity,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        identity=identity,
        feature_segment=None,
    )

    # When
    result = feature_state.type

    # Then
    assert result == IDENTITY


def test_feature_state_type__feature_segment_state__returns_feature_segment(
    segment: Segment,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        identity=None,
        feature_segment=feature_segment,
    )

    # When
    result = feature_state.type

    # Then
    assert result == FEATURE_SEGMENT


@pytest.mark.parametrize("hashed_percentage", (0.0, 30.0, 50.0, 80.0, 99.9999))
@mock.patch("features.models.get_hashed_percentage_for_object_ids")
def test_get_multivariate_feature_state_value__with_identity__returns_correct_value(  # type: ignore[no-untyped-def]
    mock_get_hashed_percentage,
    hashed_percentage,
    multivariate_feature,
    environment,
    identity,
):
    # Given
    mock_get_hashed_percentage.return_value = hashed_percentage
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )

    # When
    multivariate_value = feature_state.get_multivariate_feature_state_value(
        identity_hash_key=identity.get_hash_key()
    )

    # Then
    # we get a multivariate value
    assert multivariate_value

    # and that value is not the control (since the fixture includes values that span
    # the entire 100%)
    assert multivariate_value.value != multivariate_value.initial_value


@mock.patch.object(FeatureState, "get_multivariate_feature_state_value")
def test_get_feature_state_value__multivariate_feature__returns_mv_value(  # type: ignore[no-untyped-def]
    mock_get_mv_feature_state_value, environment, multivariate_feature, identity
):
    # Given
    value = "value"
    mock_mv_feature_state_value = mock.MagicMock(value=value)
    mock_get_mv_feature_state_value.return_value = mock_mv_feature_state_value

    environment.use_identity_composite_key_for_hashing = False
    environment.save()

    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )

    # When
    feature_state_value = feature_state.get_feature_state_value(identity=identity)

    # Then
    # the correct value is returned
    assert feature_state_value == value
    # and the correct call is made to get the multivariate feature state value
    mock_get_mv_feature_state_value.assert_called_once_with(str(identity.id))


@mock.patch.object(FeatureState, "get_multivariate_feature_state_value")
def test_get_feature_state_value__multivariate_v2_evaluation__uses_composite_key(  # type: ignore[no-untyped-def]
    mock_get_mv_feature_state_value, environment, multivariate_feature, identity
):
    # Given
    value = "value"
    mock_mv_feature_state_value = mock.MagicMock(value=value)
    mock_get_mv_feature_state_value.return_value = mock_mv_feature_state_value

    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )

    # When
    feature_state_value = feature_state.get_feature_state_value(identity=identity)

    # Then
    # the correct value is returned
    assert feature_state_value == value
    # and the correct call is made to get the multivariate feature state value
    mock_get_mv_feature_state_value.assert_called_once_with(identity.composite_key)


@pytest.mark.parametrize(
    "feature_state_version_generator",
    (
        # test the default case, this should never be true
        (None, None, None, None, False),
        # for the following 6 cases, ensure that we test in both directions
        (2, now, None, None, True),
        (None, None, 2, now, False),
        (2, now, 3, now, False),
        (3, now, 2, now, True),
        (3, now, 2, yesterday, True),
        (3, yesterday, 2, now, False),
    ),
    indirect=True,
)
def test_feature_state_gt__parametrised_versions__returns_expected(  # type: ignore[no-untyped-def]
    feature_state_version_generator,
):
    # Given / When
    # Then
    first, second, expected_result = feature_state_version_generator
    assert (first > second) is expected_result


@pytest.mark.parametrize(
    "version, live_from, expected_is_live",
    (
        (1, yesterday, True),
        (None, None, False),
        (None, yesterday, False),
        (None, tomorrow, False),
        (1, tomorrow, False),
    ),
)
def test_feature_state_is_live__parametrised_version_and_live_from__returns_expected(  # type: ignore[no-untyped-def]
    version, live_from, expected_is_live, environment
):
    # Given / When
    # Then
    assert (
        FeatureState(
            version=version, live_from=live_from, environment=environment
        ).is_live
        == expected_is_live
    )


def test_feature_state_is_live__identity_override_v2_versioning__returns_true(
    environment_v2_versioning: Environment,
    identity: Identity,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        identity=identity,
        feature=feature,
        environment=environment_v2_versioning,
    )

    # When / Then
    assert feature_state.is_live is True


def test_feature_create__prevent_flag_defaults_enabled__does_not_set_defaults(  # type: ignore[no-untyped-def]
    project, environment
):
    # Given
    project.prevent_flag_defaults = True
    project.save()

    default_state = True
    default_value = "default"

    feature = Feature(
        project=project,
        name="test_flag_defaults",
        initial_value=default_value,
        default_enabled=default_state,
    )

    # When
    feature.save()

    # Then
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    assert feature_state.enabled is False
    assert not feature_state.get_feature_state_value()


def test_feature_state_get_skip_create_audit_log__uncommitted_change_request__returns_true(  # type: ignore[no-untyped-def]
    environment, feature, admin_user
):
    # Given
    change_request = ChangeRequest.objects.create(
        environment=environment, title="Test CR", user=admin_user
    )
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        change_request=change_request,
        version=None,
    )

    # When
    result = feature_state.get_skip_create_audit_log()

    # Then
    assert result is True


def test_feature_state_get_skip_create_audit_log__environment_feature_version__returns_true(  # type: ignore[no-untyped-def]
    environment_v2_versioning: Environment, feature: Feature
):
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    feature_state = FeatureState.objects.get(
        environment=environment_v2_versioning,
        feature=feature,
        environment_feature_version=environment_feature_version,
    )

    # When
    result = feature_state.get_skip_create_audit_log()

    # Then
    assert result is True


def test_feature_state_value_get_skip_create_audit_log__environment_feature_version__returns_true(  # type: ignore[no-untyped-def]
    environment_v2_versioning: Environment, feature: Feature
):
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    feature_state = FeatureState.objects.get(
        environment=environment_v2_versioning,
        feature=feature,
        environment_feature_version=environment_feature_version,
    )

    # When
    result = feature_state.feature_state_value.get_skip_create_audit_log()

    # Then
    assert result is True


def test_feature_state_value_get_skip_create_audit_log__feature_segment_delete__returns_true(
    feature: Feature, feature_segment: FeatureSegment, environment: Environment
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        feature=feature, feature_segment=feature_segment, environment=environment
    )
    feature_state_value = feature_state.feature_state_value

    # When
    # Delete feature segment to cascade delete feature state
    # instead of soft delete
    feature_segment.delete()

    # Then
    fsv_history_instance = FeatureStateValue.history.filter(
        id=feature_state_value.id, history_type="-"
    ).first()

    assert fsv_history_instance.instance.get_skip_create_audit_log() is True


def test_feature_state_value_get_skip_create_audit_log__identity_delete__returns_true(
    feature: Feature,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        feature=feature, identity=identity, environment=environment
    )
    feature_state_value = feature_state.feature_state_value

    # When
    # Delete identity to cascade delete feature state
    # instead of soft delete
    identity.delete()

    # Then
    fsv_history_instance = FeatureStateValue.history.filter(
        id=feature_state_value.id, history_type="-"
    ).first()

    assert fsv_history_instance.instance.get_skip_create_audit_log() is True


def test_feature_state_value_get_skip_create_audit_log__feature_delete__returns_true(
    feature: Feature,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    feature_state_value = feature_state.feature_state_value

    # When
    feature.delete()

    # Then
    fsv_history_instance = FeatureStateValue.history.filter(
        id=feature_state_value.id, history_type="-"
    ).first()

    assert fsv_history_instance.instance.get_skip_create_audit_log() is True


@pytest.mark.parametrize(
    "feature_segment_id, identity_id, expected_function_name",
    (
        (1, None, "get_segment_override_created_audit_message"),
        (None, 1, "get_identity_override_created_audit_message"),
        (None, None, "get_environment_feature_state_created_audit_message"),
    ),
)
def test_feature_state_get_create_log_message__various_types__calls_correct_helper(  # type: ignore[no-untyped-def]
    mocker,
    feature_segment_id,
    identity_id,
    environment,
    feature,
    expected_function_name,
):
    # Given
    mock_audit_helpers = mocker.patch("features.models.audit_helpers")
    feature_state = FeatureState(
        feature_segment_id=feature_segment_id,
        identity_id=identity_id,
        environment=environment,
        feature=feature,
    )

    # When
    feature_state.get_create_log_message(
        mocker.MagicMock(id="history_instance")
    )  # history instance is irrelevant here

    # Then
    expected_function = getattr(mock_audit_helpers, expected_function_name)
    expected_function.assert_called_once_with(feature_state)


def test_feature_state_get_create_log_message__environment_created_after_feature__returns_none(  # type: ignore[no-untyped-def]  # noqa: E501
    feature, mocker
):
    # Given
    environment = Environment.objects.create(
        name="Test environment", project=feature.project
    )
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    # When
    log = feature_state.get_create_log_message(mocker.MagicMock())

    # Then
    assert log is None


def test_feature_state_get_create_log_message__override_after_environment_created__returns_value(  # type: ignore[no-untyped-def]  # noqa: E501
    feature, mocker, identity
):
    # Given
    environment = Environment.objects.create(
        name="Test environment", project=feature.project
    )
    feature_state = FeatureState.objects.create(
        environment=environment, feature=feature, identity=identity
    )

    # When
    log = feature_state.get_create_log_message(mocker.MagicMock())

    # Then
    assert log is not None


def test_feature_state_get_create_log_message__environment_created_before_feature__returns_message(  # type: ignore[no-untyped-def]  # noqa: E501
    environment, mocker
):
    # Given
    feature = Feature.objects.create(name="test_feature", project=environment.project)
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    # When
    log = feature_state.get_create_log_message(mocker.MagicMock())

    # Then
    assert log is not None


def test_feature_segment_update_priorities__no_changes__does_not_trigger_audit_log(  # type: ignore[no-untyped-def]
    project, environment, feature, feature_segment, admin_user, mocker
):
    # Given
    mocked_create_segment_priorities_changed_audit_log = mocker.patch(
        "features.models.create_segment_priorities_changed_audit_log"
    )

    another_segment = Segment.objects.create(project=project, name="Another segment")
    FeatureSegment.objects.create(
        feature=feature,
        segment=another_segment,
        environment=environment,
        priority=feature_segment.priority + 1,
    )

    existing_feature_segments = FeatureSegment.objects.filter(
        environment=environment, feature=feature
    )
    existing_id_priority_pairs = FeatureSegment.to_id_priority_tuple_pairs(
        existing_feature_segments
    )

    # When
    returned_feature_segments = FeatureSegment.update_priorities(
        new_feature_segment_id_priorities=existing_id_priority_pairs
    )

    # Then
    assert list(returned_feature_segments) == list(existing_feature_segments)

    mocked_create_segment_priorities_changed_audit_log.delay.assert_not_called()


def test_feature_segment_update_priorities__with_changes__triggers_audit_log(  # type: ignore[no-untyped-def]
    project, environment, feature, feature_segment, admin_user, mocker
):
    # Given
    mocked_create_segment_priorities_changed_audit_log = mocker.patch(
        "features.models.create_segment_priorities_changed_audit_log"
    )
    mocked_historical_records = mocker.patch("features.models.HistoricalRecords")
    mocked_request = mocker.MagicMock()
    mocked_historical_records.thread.request = mocked_request

    another_segment = Segment.objects.create(project=project, name="Another segment")
    another_feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=another_segment,
        environment=environment,
        priority=feature_segment.priority + 1,
    )

    existing_id_priority_pairs = FeatureSegment.to_id_priority_tuple_pairs(
        feature.feature_segments.filter(environment=environment)
    )
    new_id_priority_pairs = [(feature_segment.id, 1), (another_feature_segment.id, 0)]

    # When
    with freezegun.freeze_time(now):
        returned_feature_segments = FeatureSegment.update_priorities(
            new_feature_segment_id_priorities=new_id_priority_pairs
        )

    # Then
    assert sorted(
        FeatureSegment.to_id_priority_tuple_pairs(returned_feature_segments),
        key=lambda t: t[1],
    ) == sorted(new_id_priority_pairs, key=lambda t: t[1])

    mocked_create_segment_priorities_changed_audit_log.delay.assert_called_once_with(
        kwargs={
            "previous_id_priority_pairs": existing_id_priority_pairs,
            "feature_segment_ids": [feature_segment.id, another_feature_segment.id],
            "user_id": mocked_request.user.id,
            "master_api_key_id": mocked_request.master_api_key.id,
            "changed_at": now.isoformat(),
        }
    )


def test_feature_state_gt__multiple_segment_override_versions__higher_version_wins(  # type: ignore[no-untyped-def]
    feature, segment, feature_segment, environment
):
    # Given
    v1_segment_override = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )
    v2_segment_override = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        version=2,
    )

    # When
    result = v2_segment_override > v1_segment_override

    # Then
    assert result is True


def test_feature_state_gt__segment_override_vs_environment_default__segment_wins(  # type: ignore[no-untyped-def]
    feature, segment, feature_segment, environment
):
    # Given
    segment_override = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )
    environment_default = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    # When
    result = segment_override > environment_default

    # Then
    assert result is True


def test_feature_state_clone__segment_override__clones_feature_segment(
    feature: Feature,
    segment_featurestate: FeatureState,
    environment: Environment,
    environment_two: Environment,
) -> None:
    # Given
    original_feature_segment = segment_featurestate.feature_segment

    # When
    cloned_fs = segment_featurestate.clone(env=environment_two, as_draft=True)

    # Then
    assert cloned_fs.feature_segment != original_feature_segment

    assert (
        cloned_fs.feature_segment.segment  # type: ignore[union-attr]
        == segment_featurestate.feature_segment.segment  # type: ignore[union-attr]
    )
    assert (
        cloned_fs.feature_segment.priority  # type: ignore[union-attr]
        == segment_featurestate.feature_segment.priority  # type: ignore[union-attr]
    )


def test_feature_segment_clone__to_different_environment__copies_attributes(
    feature_segment: FeatureSegment,
    environment: Environment,
    environment_two: Environment,
) -> None:
    # Given
    original_id = feature_segment.id

    # When
    cloned_feature_segment = feature_segment.clone(environment=environment_two)

    # Then
    assert cloned_feature_segment.id != original_id

    assert cloned_feature_segment.priority == feature_segment.priority
    assert cloned_feature_segment.segment == feature_segment.segment
    assert cloned_feature_segment.feature == feature_segment.feature
    assert cloned_feature_segment.environment == environment_two


def test_feature_create__v2_versioning_environments__creates_feature_states_and_versions(
    project: "Project",
) -> None:
    # Given
    Environment.objects.create(
        project=project, name="Environment 1", use_v2_feature_versioning=True
    )
    Environment.objects.create(
        project=project, name="Environment 2", use_v2_feature_versioning=True
    )

    # When
    feature = Feature.objects.create(name="test_feature", project=project)

    # Then
    assert EnvironmentFeatureVersion.objects.filter(feature=feature).count() == 2
    assert feature.feature_states.count() == 2


def test_feature_state_save__updated_state__triggers_webhooks(
    mocker: MockerFixture,
    feature_state: FeatureState,
    admin_history: None,
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "features.tasks.trigger_feature_state_change_webhooks"
    )

    # When
    feature_state.enabled = not feature_state.enabled
    # Feature state saved with admin history thread context
    feature_state.save()

    # Then - Webhook is triggered via AuditLog signal chain
    mock_trigger_feature_state_change_webhooks.assert_called_once()
    called_feature_state = mock_trigger_feature_state_change_webhooks.call_args[0][0]
    assert called_feature_state.id == feature_state.id


def test_feature_state_create__segment_override__triggers_webhooks(
    mocker: MockerFixture,
    feature: Feature,
    environment: Environment,
    feature_segment: FeatureSegment,
    admin_history: None,
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "features.tasks.trigger_feature_state_change_webhooks"
    )
    # Get the environment default enabled state and create with the opposite
    # to ensure an AuditLog is created (otherwise no AuditLog is created for
    # segment overrides that match the environment default)
    env_default = FeatureState.objects.get(
        feature=feature, environment=environment, feature_segment__isnull=True
    )
    override_enabled = not env_default.enabled

    # When
    # Feature state created with admin history thread context
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=override_enabled,
    )

    # Then - Webhook is triggered via AuditLog signal chain
    mock_trigger_feature_state_change_webhooks.assert_called_once()
    called_feature_state = mock_trigger_feature_state_change_webhooks.call_args[0][0]
    assert called_feature_state.id == feature_state.id


def test_feature_state_create__with_environment_feature_version__does_not_trigger_webhooks(
    mocker: MockerFixture,
    feature: Feature,
    environment_v2_versioning: Environment,
    segment: Segment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "features.tasks.trigger_feature_state_change_webhooks"
    )

    # When
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    feature_segment = FeatureSegment.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        segment=segment,
        environment_feature_version=new_version,
    )
    FeatureState.objects.create(
        feature=feature,
        environment_feature_version=new_version,
        environment=environment_v2_versioning,
        feature_segment=feature_segment,
    )
    new_version.publish(admin_user)

    # Then - Webhooks are not triggered for versioned environments
    # (handled by trigger_update_version_webhooks instead)
    mock_trigger_feature_state_change_webhooks.assert_not_called()
