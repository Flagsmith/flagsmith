import json
from datetime import datetime
from typing import Any

import requests
import structlog
from django.core.serializers.json import DjangoJSONEncoder

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.services import get_audited_instance_from_audit_log_record
from core.signing import sign_payload
from features.models import FeatureState
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from integrations.sentry.models import SentryChangeTrackingConfiguration
from util.util import postpone

logger = structlog.get_logger("sentry_change_tracking")

_DEFAULT_AUTHOR_EMAIL = "app@flagsmith.com"


def process_audit_log(audit_log: AuditLog) -> None:
    """
    Public entry point for v2 Sentry change tracking. Given an audit log row
    from any feature-related event, dispatches to the right handler and posts
    per-FS Sentry events. The signal handler in ``audit.signals`` just passes
    the audit log; the rest of the orchestration lives here.
    """
    if audit_log.related_object_type == RelatedObjectType.EF_VERSION.name:
        _process_efv_audit_log(audit_log)
    elif audit_log.related_object_type == RelatedObjectType.FEATURE.name:
        _process_feature_audit_log(audit_log)


def _process_efv_audit_log(audit_log: AuditLog) -> None:
    """v2 publish (env-default toggle, segment override, scheduled change)."""
    from features.versioning.models import EnvironmentFeatureVersion
    from features.versioning.versioning_service import (
        get_feature_state_match_key,
        get_updated_feature_states_for_version,
    )

    if (
        audit_log.environment is None
        or not audit_log.environment.use_v2_feature_versioning
    ):
        return

    config = _get_config_for_environment(audit_log.environment)
    if not config:
        return

    if not audit_log.related_object_uuid:
        return

    try:
        efv = EnvironmentFeatureVersion.objects.select_related("feature").get(
            uuid=audit_log.related_object_uuid,
        )
    except EnvironmentFeatureVersion.DoesNotExist:
        return

    changed_feature_states = get_updated_feature_states_for_version(efv)
    if not changed_feature_states:
        return

    previous_version = efv.get_previous_version()
    previous_fs_keys = (
        {
            get_feature_state_match_key(fs)
            for fs in previous_version.feature_states.all()
        }
        if previous_version
        else set()
    )

    timestamp = efv.live_from or efv.published_at or audit_log.created_date
    author_email = _author_email_for_audit_log(audit_log)
    flag_name = efv.feature.name

    events = [
        SentryChangeTracking.build_payload_entry(
            action=(
                "updated"
                if get_feature_state_match_key(fs) in previous_fs_keys
                else "created"
            ),
            flag_name=flag_name,
            change_id=fs.pk,
            timestamp=timestamp,
            author_email=author_email,
        )
        for fs in changed_feature_states
    ]
    _post_events(config, events)


def _process_feature_audit_log(audit_log: AuditLog) -> None:
    """
    v2 flag-create. The FEATURE audit row is project-wide, so fan out per
    v2 env in the project that has Sentry configured. The audit-log task
    runs ~1s after feature creation in production (see
    ``core.signals.create_audit_log_from_historical_record``'s ``delay_until``),
    so by the time this runs, the FSes exist.
    """
    from features.models import Feature

    history_record = audit_log.history_record
    if history_record is None or history_record.history_type != "+":
        return

    feature = get_audited_instance_from_audit_log_record(audit_log)
    if not isinstance(feature, Feature):
        return

    if not audit_log.project_id:
        return

    sentry_configs = SentryChangeTrackingConfiguration.objects.filter(
        environment__project_id=audit_log.project_id,
        environment__use_v2_feature_versioning=True,
        deleted_at__isnull=True,
    ).select_related("environment")

    author_email = _author_email_for_audit_log(audit_log)

    for config in sentry_configs:
        # Mirror v1's env-create suppression from
        # FeatureState.get_create_log_message: skip when the env was created
        # after the feature (env-create / env-clone scenarios).
        if config.environment.created_date > feature.created_date:
            continue

        fs = FeatureState.objects.filter(
            feature=feature,
            environment=config.environment,
            feature_segment__isnull=True,
            identity__isnull=True,
        ).first()
        if not fs:
            continue

        timestamp = max(fs.live_from, fs.updated_at) if fs.live_from else fs.updated_at
        events = [
            SentryChangeTracking.build_payload_entry(
                action="created",
                flag_name=feature.name,
                change_id=fs.pk,
                timestamp=timestamp,
                author_email=author_email,
            )
        ]
        _post_events(config, events)


def _get_config_for_environment(
    environment: Any,
) -> SentryChangeTrackingConfiguration | None:
    config: SentryChangeTrackingConfiguration | None = (
        SentryChangeTrackingConfiguration.objects.filter(
            environment=environment,
            deleted_at__isnull=True,
        ).first()
    )
    return config


def _author_email_for_audit_log(audit_log: AuditLog | None) -> str:
    if audit_log is None:
        return _DEFAULT_AUTHOR_EMAIL
    return getattr(audit_log.author, "email", _DEFAULT_AUTHOR_EMAIL)


def _post_events(
    config: SentryChangeTrackingConfiguration,
    events: list[dict[str, Any]],
) -> None:
    if not events:
        return
    SentryChangeTracking(
        webhook_url=config.webhook_url,
        secret=config.secret,
    ).track_events_async(events)


class SentryChangeTracking(AbstractBaseEventIntegrationWrapper):
    """
    Change Tracking integration with Sentry

    Spec: https://github.com/getsentry/sentry/blob/master/src/sentry/flags/docs/api.md#create-generic-flag-log-post

    NOTE: This triggers when...
    - ...creating the flag because there is a hook to create (save) the initial feature state.
    - ...updating the flag because there is a signal to trigger this on model save.
    - ...deleting the flag because deleting means saving the model instance with a deleted_at timestamp.
    """

    def __init__(self, webhook_url: str, secret: str) -> None:
        self.webhook_url = webhook_url
        self.secret = secret

    @staticmethod
    def build_payload_entry(
        *,
        action: str,
        flag_name: str,
        change_id: Any,
        timestamp: datetime,
        author_email: str,
    ) -> dict[str, Any]:
        """Shared shape for a single `data[]` entry in a Sentry flag-log payload."""
        return {
            "action": action,
            "flag": flag_name,
            "created_at": timestamp.isoformat(timespec="seconds"),
            "created_by": {"id": author_email, "type": "email"},
            "change_id": str(change_id),
        }

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict[str, Any]:
        feature_state = get_audited_instance_from_audit_log_record(audit_log_record)
        if not isinstance(feature_state, FeatureState):  # pragma: no cover
            logger.warning(
                f"{type(feature_state)} is not supported by Sentry Change Tracking integration."
            )
            return {}

        timestamp = feature_state.deleted_at or (
            max(feature_state.live_from, feature_state.updated_at)
            if feature_state.live_from
            else feature_state.updated_at
        )

        action = {
            "+": "created",
            "-": "deleted",
            "~": "updated",
        }[audit_log_record.history_record.history_type]  # type: ignore[union-attr]

        return SentryChangeTracking.build_payload_entry(
            action=action,
            flag_name=feature_state.feature.name,
            change_id=feature_state.pk,
            timestamp=timestamp,
            author_email=getattr(
                audit_log_record.author, "email", _DEFAULT_AUTHOR_EMAIL
            ),
        )

    def _track_event(self, event: dict[str, Any]) -> None:
        self._send_events([event])

    @postpone  # type: ignore[misc]
    def track_events_async(self, events: list[dict[str, Any]]) -> None:
        self._send_events(events)

    def _send_events(self, events: list[dict[str, Any]]) -> None:
        if not events:
            return

        # All entries in a batched payload share the same flag (one EFV = one feature).
        first_event = events[0]
        action = first_event["action"]
        feature_name = first_event["flag"]

        log = logger.bind(
            sentry_action=action,
            feature_name=feature_name,
        )

        payload = {
            "data": events,
            "meta": {"version": 1},
        }
        json_payload = json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder)

        headers = {
            "Content-Type": "application/json",
            "X-Sentry-Signature": sign_payload(json_payload, self.secret),
        }

        log.debug(
            "sending",
            url=self.webhook_url,
            headers=headers,
            payload=payload,
        )

        try:
            response = requests.post(
                url=self.webhook_url,
                headers=headers,
                data=json_payload,
            )
            response.raise_for_status()  # NOTE: This is for future-proofing, as Sentry won't respond 4xx.
        except requests.exceptions.RequestException as error:
            log.warning(
                "request-failure",
                error=error,
            )
            return

        if not response.text:  # This is fragile and undocumented. ¯\_(ツ)_/¯
            log.info("success")
            return

        log.warning(
            "integration-error",
            sentry_response_status=response.status_code,
            sentry_response_body=response.text,
        )
