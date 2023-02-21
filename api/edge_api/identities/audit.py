import typing

from flag_engine.features.models import FeatureStateModel

from audit.models import AuditLog
from environments.models import Environment

if typing.TYPE_CHECKING:
    from edge_api.identities.models import EdgeIdentity


def generate_change_dict(
    change_type: str,
    identity: "EdgeIdentity",
    new: typing.Optional[FeatureStateModel] = None,
    old: typing.Optional[FeatureStateModel] = None,
):
    if not (new or old):
        raise ValueError("Must provide one of 'current' or 'previous'")

    change_dict = {"change_type": change_type}
    if new:
        change_dict["new"] = {
            "enabled": new.enabled,
            "value": new.get_value(identity.id),
        }
    if old:
        change_dict["old"] = {
            "enabled": old.enabled,
            "value": old.get_value(identity.id),
        }

    return change_dict


def generate_audit_log_records(
    environment_api_key: str, identifier: str, user_id: int, changes: dict
):
    audit_records = []

    feature_override_changes = changes.get("feature_overrides")
    if not feature_override_changes:
        return

    environment = Environment.objects.select_related(
        "project", "project__organisation"
    ).get(api_key=environment_api_key)

    for feature_name, change_details in feature_override_changes.items():
        action = {"+": "created", "-": "removed", "~": "deleted"}.get(
            change_details.get("change_type")
        )
        log = f"Feature override {action} for feature '{feature_name}' and identity '{identifier}'"
        audit_records.append(
            AuditLog(
                project=environment.project,
                environment=environment,
                log=log,
                author_id=user_id,
            )
        )

    AuditLog.objects.bulk_create(audit_records)
