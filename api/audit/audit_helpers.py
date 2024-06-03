from contextlib import suppress

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion


def get_related_feature_id(audit_log_record: AuditLog) -> int | None:
    """
    Given an AuditLog record, return the related feature id if applicable.
    """

    feature_id = None

    with suppress(EnvironmentFeatureVersion.DoesNotExist, FeatureState.DoesNotExist):
        match audit_log_record.related_object_type:
            case RelatedObjectType.FEATURE.name:
                feature_id = audit_log_record.related_object_id
            case RelatedObjectType.EF_VERSION.name:
                ef_version = EnvironmentFeatureVersion.objects.get(
                    uuid=audit_log_record.related_object_uuid
                )
                feature_id = ef_version.feature_id
            case RelatedObjectType.FEATURE_STATE.name:
                feature_state = FeatureState.objects.get(
                    id=audit_log_record.related_object_id
                )
                feature_id = feature_state.feature_id

    return feature_id
