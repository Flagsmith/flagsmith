from audit.models import AuditLog
from audit.services import get_audited_instance_from_audit_log_record
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.versioning.models import EnvironmentFeatureVersion
from integrations.grafana.types import GrafanaAnnotation
from segments.models import Segment


def _get_feature_tags(
    feature: Feature,
) -> list[str]:
    return list(feature.tags.values_list("label", flat=True))


def _get_instance_tags_from_audit_log_record(
    audit_log_record: AuditLog,
) -> list[str]:
    if instance := get_audited_instance_from_audit_log_record(audit_log_record):
        if isinstance(instance, Feature):
            return [
                f"feature:{instance.name}",
                *_get_feature_tags(instance),
            ]

        if isinstance(instance, FeatureState):
            return [
                f"feature:{(feature := instance.feature).name}",
                f'flag:{"enabled" if instance.enabled else "disabled"}',
                *_get_feature_tags(feature),
            ]

        if isinstance(instance, FeatureStateValue):
            return [
                f"feature:{(feature := instance.feature_state.feature).name}",
                *_get_feature_tags(feature),
            ]

        if isinstance(instance, Segment):
            return [f"segment:{instance.name}"]

        if isinstance(instance, FeatureSegment):
            return [
                f"feature:{(feature := instance.feature).name}",
                f"segment:{instance.segment.name}",
                *_get_feature_tags(feature),
            ]

        if isinstance(instance, EnvironmentFeatureVersion):
            return [
                f"feature:{instance.feature.name}",
                *_get_feature_tags(instance.feature),
            ]

    return []


def map_audit_log_record_to_grafana_annotation(
    audit_log_record: AuditLog,
) -> GrafanaAnnotation:
    tags = [
        "flagsmith",
        f"project:{audit_log_record.project_name}",
        f"environment:{audit_log_record.environment_name}",
        f"by:{audit_log_record.author_identifier}",
        *_get_instance_tags_from_audit_log_record(audit_log_record),
    ]
    time = int(audit_log_record.created_date.timestamp() * 1000)  # ms since epoch

    return {
        "tags": tags,
        "text": audit_log_record.log,
        "time": time,
        "timeEnd": time,
    }
