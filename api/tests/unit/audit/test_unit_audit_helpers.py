from audit.audit_helpers import get_related_feature_id
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from segments.models import Segment


def test_get_related_feature_id_for_feature_audit_log(
    feature: Feature, environment: Environment
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        environment=environment,
        related_object_id=feature.id,
        related_object_type=RelatedObjectType.FEATURE.name,
        log="Test",
    )

    # When
    related_feature_id = get_related_feature_id(audit_log_record)

    # Then
    assert related_feature_id == feature.id


def test_get_related_feature_id_for_environment_feature_version_audit_log(
    environment_v2_versioning: Environment, feature: Feature
) -> None:
    # Given
    ef_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    audit_log_record = AuditLog.objects.create(
        environment=environment_v2_versioning,
        related_object_uuid=ef_version.uuid,
        related_object_type=RelatedObjectType.EF_VERSION.name,
        log="Test",
    )

    # When
    related_feature_id = get_related_feature_id(audit_log_record)

    # Then
    assert related_feature_id == feature.id


def test_get_related_feature_id_for_feature_state_audit_log(
    environment: Environment, feature: Feature
) -> None:
    # Given
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    audit_log_record = AuditLog.objects.create(
        environment=environment,
        related_object_id=feature_state.id,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        log="Test",
    )

    # When
    related_feature_id = get_related_feature_id(audit_log_record)

    # Then
    assert related_feature_id == feature.id


def test_get_related_feature_id_returns_none_for_entities_with_no_related_feature(
    segment: Segment, feature: Feature
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=segment.project,
        related_object_id=segment.id,
        related_object_type=RelatedObjectType.SEGMENT.name,
        log="Test",
    )

    # When
    related_feature_id = get_related_feature_id(audit_log_record)

    # Then
    assert related_feature_id is None


def test_get_related_feature_id_returns_none_when_related_object_not_found(
    environment: Environment,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        environment=environment,
        related_object_id=1,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        log="Test",
    )

    # When
    related_feature_id = get_related_feature_id(audit_log_record)

    # Then
    assert related_feature_id is None
