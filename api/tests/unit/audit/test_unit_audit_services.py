from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.services import get_audited_instance_from_audit_log_record
from audit.tasks import (
    create_feature_state_updated_by_change_request_audit_log,
    create_segment_priorities_changed_audit_log,
)
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import (
    create_environment_feature_version_published_audit_log_task,
)
from features.workflows.core.models import ChangeRequest


def test_get_audited_instance_from_audit_log_record__change_request__return_expected(
    change_request_feature_state: FeatureState,
) -> None:
    # Given
    create_feature_state_updated_by_change_request_audit_log(
        change_request_feature_state.id
    )
    audit_log_record = AuditLog.objects.get(
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        related_object_id=change_request_feature_state.id,
    )
    change_request_feature_state.delete()

    # When
    instance = get_audited_instance_from_audit_log_record(audit_log_record)

    # Then
    assert instance == change_request_feature_state


def test_get_audited_instance_from_audit_log_record__segment_priorities__return_expected(
    feature: Feature,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    create_segment_priorities_changed_audit_log(
        previous_id_priority_pairs=[
            (feature_segment.id, 0),
        ],
        feature_segment_ids=[feature_segment.id],
    )
    audit_log_record = AuditLog.objects.get(
        related_object_type=RelatedObjectType.FEATURE.name,
        related_object_id=feature.id,
    )
    feature.delete()

    # When
    instance = get_audited_instance_from_audit_log_record(audit_log_record)

    # Then
    assert instance == feature


def test_get_audited_instance_from_audit_log_record__feature_versioning__return_expected(
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
    )
    create_environment_feature_version_published_audit_log_task(version.uuid)
    audit_log_record = AuditLog.objects.get(
        related_object_type=RelatedObjectType.EF_VERSION.name,
        related_object_uuid=version.uuid,
    )
    version.delete()

    # When
    instance = get_audited_instance_from_audit_log_record(audit_log_record)

    # Then
    assert instance == version


def test_get_audited_instance_from_audit_log_record__historical_record__return_expected(
    change_request: ChangeRequest,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.get(
        related_object_type=RelatedObjectType.CHANGE_REQUEST.name,
        related_object_id=change_request.id,
    )
    change_request.delete()

    # When
    instance = get_audited_instance_from_audit_log_record(audit_log_record)

    # Then
    assert instance == change_request


def test_get_audited_instance_from_audit_log_record__unexpected_audit_log__return_none(
    change_request: ChangeRequest,
) -> None:
    # Given
    # A change request log was created not via history
    audit_log_record = AuditLog.objects.create(
        history_record_id=None,
        related_object_id=change_request.id,
        related_object_type=RelatedObjectType.CHANGE_REQUEST.name,
    )

    # When
    instance = get_audited_instance_from_audit_log_record(audit_log_record)

    # Then
    assert instance is None
