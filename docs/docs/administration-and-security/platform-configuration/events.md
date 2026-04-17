---
title: Events
sidebar_label: Events
sidebar_position: 30
---

Flagsmith backend emits [OpenTelemetry events](https://opentelemetry.io/docs/specs/otel/logs/data-model/#events)
that can be ingested to downstream observability systems and/or a data warehouse of your choice via OTLP.
To learn how to configure this, see [OpenTelemetry](deployment-self-hosting/scaling-and-performance/opentelemetry).

## Event catalog

### `app_analytics.no-analytics-database-configured`

Logged at `warning` from:
 - `api/app_analytics/analytics_db_service.py:74`
 - `api/app_analytics/analytics_db_service.py:210`

Attributes:
 - `details`

### `code_references.cleanup_issues.created`

Logged at `info` from:
 - `api/integrations/github/views.py:388`

Attributes:
 - `issues_created.count`
 - `organisation.id`

### `code_references.scan.created`

Logged at `info` from:
 - `api/projects/code_references/views.py:41`

Attributes:
 - `code_references.count`
 - `feature.count`
 - `organisation.id`

### `dynamodb.environment-document-compressed`

Logged at `info` from:
 - `api/environments/dynamodb/wrappers/environment_wrapper.py:92`

Attributes:
 - `environment_api_key`
 - `environment_id`

### `feature_health.feature-health-event-dismissal-not-supported`

Logged at `warning` from:
 - `api/features/feature_health/services.py:127`

Attributes:
 - `feature_health_event_external_id`
 - `feature_health_event_id`
 - `feature_health_event_type`
 - `provider_name`

### `feature_health.feature-health-provider-error`

Logged at `error` from:
 - `api/features/feature_health/services.py:50`

Attributes:
 - `exc_info`
 - `provider_id`
 - `provider_name`

### `feature_health.invalid-feature-health-webhook-path-requested`

Logged at `warning` from:
 - `api/features/feature_health/providers/services.py:30`

Attributes:
 - `path`

### `gitlab.api-call-failed`

Logged at `error` from:
 - `api/integrations/gitlab/views/browse_gitlab.py:58`

Attributes:
 - `exc_info`

### `gitlab.configuration-created`

Logged at `info` from:
 - `api/integrations/gitlab/views/configuration.py:26`

Attributes:
 - `gitlab_instance_url`
 - `organisation.id`
 - `project.id`

### `gitlab.configuration-updated`

Logged at `info` from:
 - `api/integrations/gitlab/views/configuration.py:34`

Attributes:
 - `gitlab_instance_url`
 - `organisation.id`
 - `project.id`

### `gitlab.issues-fetched`

Logged at `info` from:
 - `api/integrations/gitlab/views/browse_gitlab.py:133`

Attributes:
 - `gitlab_project_id`
 - `project.id`

### `gitlab.merge-requests-fetched`

Logged at `info` from:
 - `api/integrations/gitlab/views/browse_gitlab.py:159`

Attributes:
 - `gitlab_project_id`
 - `project.id`

### `gitlab.projects-fetched`

Logged at `info` from:
 - `api/integrations/gitlab/views/browse_gitlab.py:108`

Attributes:
 - `project.id`

### `launch_darkly.import-failed`

Logged at `exception` from:
 - `api/integrations/launch_darkly/tasks.py:36`

Attributes:
 - `import_request_id`
 - `ld_project_key`
 - `organisation_id`
 - `project_id`

### `launch_darkly.import-rate-limit-reached`

Logged at `warning` from:
 - `api/integrations/launch_darkly/tasks.py:26`

Attributes:
 - `error_message`
 - `import_request_id`
 - `ld_project_key`
 - `organisation_id`
 - `project_id`
 - `retry_at`

### `platform_hub.no-analytics-database-configured`

Logged at `warning` from:
 - `api/platform_hub/services.py:116`
 - `api/platform_hub/services.py:206`
 - `api/platform_hub/services.py:428`

Attributes:

### `segments.serializers.segment-revision-created`

Logged at `info` from:
 - `api/segments/serializers.py:141`

Attributes:
 - `revision_id`
 - `segment_id`

### `sentry_change_tracking.integration-error`

Logged at `warning` from:
 - `api/integrations/sentry/change_tracking.py:112`

Attributes:
 - `feature_name`
 - `sentry_action`
 - `sentry_response_body`
 - `sentry_response_status`

### `sentry_change_tracking.request-failure`

Logged at `warning` from:
 - `api/integrations/sentry/change_tracking.py:102`

Attributes:
 - `error`
 - `feature_name`
 - `sentry_action`

### `sentry_change_tracking.sending`

Logged at `debug` from:
 - `api/integrations/sentry/change_tracking.py:87`

Attributes:
 - `feature_name`
 - `headers`
 - `payload`
 - `sentry_action`
 - `url`

### `sentry_change_tracking.success`

Logged at `info` from:
 - `api/integrations/sentry/change_tracking.py:109`

Attributes:
 - `feature_name`
 - `sentry_action`

### `workflows.change_request.committed`

Logged at `info` from:
 - `api/core/workflows_services.py:39`

Attributes:
 - `environment.id`
 - `feature_states.count`
 - `organisation.id`

### `workflows.missing-live-segment`

Logged at `warning` from:
 - `api/core/workflows_services.py:114`

Attributes:
 - `draft_segment`

### `workflows.segment-revision-created`

Logged at `info` from:
 - `api/core/workflows_services.py:119`

Attributes:
 - `revision_id`
 - `segment_id`

