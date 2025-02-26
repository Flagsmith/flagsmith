from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.models import AbstractBaseAuditableModel
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion


def get_audited_instance_from_audit_log_record(
    audit_log_record: AuditLog,
) -> AbstractBaseAuditableModel | None:
    """
    Given an `AuditLog` model instance, return a model instance that produced the log.
    """
    # There's currently four (sigh) ways an audit log record is created:
    # 1. Historical record
    # 2. Segment priorities changed
    # 3. Change request
    # 4. Environment feature version published

    # Try getting the historical record first.
    if history_record := audit_log_record.history_record:
        return history_record.instance  # type: ignore[attr-defined,no-any-return]

    # Try to infer the model class from `AuditLog.related_object_type`.
    match audit_log_record.related_object_type:
        # Assume segment priorities change.
        case RelatedObjectType.FEATURE.name:
            return (  # type: ignore[no-any-return]
                Feature.objects.all_with_deleted()
                .filter(
                    pk=audit_log_record.related_object_id,
                    project=audit_log_record.project,
                )
                .first()
            )

        # Assume change request.
        case RelatedObjectType.FEATURE_STATE.name:
            return (  # type: ignore[no-any-return]
                FeatureState.objects.all_with_deleted()
                .filter(
                    pk=audit_log_record.related_object_id,
                    environment=audit_log_record.environment,
                )
                .first()
            )

        # Assume environment feature version.
        case RelatedObjectType.EF_VERSION.name:
            return (  # type: ignore[no-any-return]
                EnvironmentFeatureVersion.objects.all_with_deleted()
                .filter(
                    uuid=audit_log_record.related_object_uuid,
                    environment=audit_log_record.environment,
                )
                .select_related("feature")
                .first()
            )

    # All known audit log sources exhausted by now.
    # Since `RelatedObjectType` is not a 1:1 mapping to a model class,
    # generalised heuristics might be dangerous.
    return None
