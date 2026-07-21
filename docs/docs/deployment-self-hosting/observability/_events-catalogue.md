
### `api_usage.notification.evaluated`

Logged at `info` from:
 - `api/organisations/task_helpers.py:153`

Attributes:
 - `allowed_api_calls`
 - `api_usage`
 - `api_usage_percent`
 - `matched_threshold`
 - `organisation.id`
 - `period_ends_at`
 - `period_starts_at`

### `api_usage.notification.missing_billing_starts_at`

Logged at `error` from:
 - `api/organisations/task_helpers.py:118`

Attributes:
 - `organisation.id`

### `api_usage.notification.sent`

Logged at `info` from:
 - `api/organisations/task_helpers.py:176`

Attributes:
 - `matched_threshold`
 - `organisation.id`

### `app_analytics.no_analytics_database_configured`

Logged at `warning` from:
 - `api/app_analytics/analytics_db_service.py:74`
 - `api/app_analytics/analytics_db_service.py:187`
 - `api/app_analytics/analytics_db_service.py:278`

Attributes:
 - `details`

### `billing.seat.added`

Logged at `info` from:
 - `api/organisations/chargebee/chargebee.py:239`

Attributes:
 - `addon.id`
 - `organisation.id`
 - `seats.new`
 - `seats.previous`
 - `subscription.id`

### `code_references.cleanup_issues.created`

Logged at `info` from:
 - `api/integrations/github/views.py:388`

Attributes:
 - `issues_created.count`
 - `organisation.id`

### `code_references.scan.created`

Logged at `info` from:
 - `api/projects/code_references/views.py:61`

Attributes:
 - `code_references.count`
 - `feature.count`
 - `organisation.id`

### `core.encrypted_field.decrypt_failed`

Logged at `warning` from:
 - `api/core/fields.py:37`

Attributes:
 - `exc_info`

### `dynamodb.environment_document_compressed`

Logged at `info` from:
 - `api/environments/dynamodb/wrappers/environment_wrapper.py:92`

Attributes:
 - `environment_api_key`
 - `environment_id`

### `experimentation.exposures.compute_failed`

Logged at `error` from:
 - `api/experimentation/tasks.py:100`

Attributes:
 - `environment.id`
 - `exc_info`
 - `experiment.id`
 - `feature.id`
 - `organisation.id`

### `experimentation.ingestion_infra.bucket_created`

Logged at `info` from:
 - `api/experimentation/ingestion_infra_service.py:95`

Attributes:
 - `bucket.name`
 - `organisation.id`

### `experimentation.ingestion_infra.stream_created`

Logged at `info` from:
 - `api/experimentation/ingestion_infra_service.py:186`

Attributes:
 - `bucket.name`
 - `organisation.id`
 - `stream.name`

### `experimentation.results.compute_failed`

Logged at `error` from:
 - `api/experimentation/tasks.py:136`

Attributes:
 - `environment.id`
 - `exc_info`
 - `experiment.id`
 - `organisation.id`

### `feature_health.feature_health_event_dismissal_not_supported`

Logged at `warning` from:
 - `api/features/feature_health/services.py:127`

Attributes:
 - `feature_health_event_external_id`
 - `feature_health_event_id`
 - `feature_health_event_type`
 - `provider_name`

### `feature_health.feature_health_provider_error`

Logged at `error` from:
 - `api/features/feature_health/services.py:50`

Attributes:
 - `exc_info`
 - `provider_id`
 - `provider_name`

### `feature_health.invalid_feature_health_webhook_path_requested`

Logged at `warning` from:
 - `api/features/feature_health/providers/services.py:30`

Attributes:
 - `path`

### `feature_lifecycle.summarised`

Logged at `info` from:
 - `api/features/feature_lifecycle/views.py:52`

Attributes:
 - `environment.id`
 - `organisation.id`

### `gitlab.api_call.failed`

Logged at `error` from:
 - `api/integrations/gitlab/views/browse_gitlab.py:59`

Attributes:
 - `exc_info`
 - `organisation.id`
 - `project.id`

### `gitlab.comment.post_failed`

Logged at `warning` from:
 - `api/integrations/gitlab/services/comments.py:69`

Attributes:
 - `exc_info`
 - `feature.id`
 - `gitlab.project.path`
 - `gitlab.resource.iid`
 - `organisation.id`
 - `project.id`

### `gitlab.comment.posted`

Logged at `info` from:
 - `api/integrations/gitlab/services/comments.py:71`

Attributes:
 - `feature.id`
 - `gitlab.project.path`
 - `gitlab.resource.iid`
 - `organisation.id`
 - `project.id`

### `gitlab.configuration.created`

Logged at `info` from:
 - `api/integrations/gitlab/views/configuration.py:26`

Attributes:
 - `gitlab_instance_url`
 - `organisation.id`
 - `project.id`

### `gitlab.configuration.updated`

Logged at `info` from:
 - `api/integrations/gitlab/views/configuration.py:34`

Attributes:
 - `gitlab_instance_url`
 - `organisation.id`
 - `project.id`

### `gitlab.label.created`

Logged at `info` from:
 - `api/integrations/gitlab/services/labels.py:66`

Attributes:
 - `feature.id`
 - `gitlab_project.path`
 - `organisation.id`
 - `project.id`
 - `resource.iid`
 - `resource.type`

### `gitlab.label.failed`

Logged at `exception` from:
 - `api/integrations/gitlab/services/labels.py:76`

Attributes:
 - `feature.id`
 - `gitlab_project.path`
 - `organisation.id`
 - `project.id`
 - `resource.iid`
 - `resource.type`

### `gitlab.label.removal_failed`

Logged at `exception` from:
 - `api/integrations/gitlab/tasks.py:189`

Attributes:
 - `feature.id`
 - `gitlab_project.path`
 - `project.id`
 - `resource.iid`
 - `resource.type`

### `gitlab.label.removed`

Logged at `info` from:
 - `api/integrations/gitlab/tasks.py:187`

Attributes:
 - `feature.id`
 - `gitlab_project.path`
 - `project.id`
 - `resource.iid`
 - `resource.type`

### `gitlab.resource.linked`

Logged at `info` from:
 - `api/integrations/vcs/services.py:35`

Attributes:
 - `feature.id`
 - `organisation.id`
 - `project.id`
 - `resource.type`

### `gitlab.resource.unlinked`

Logged at `info` from:
 - `api/integrations/vcs/services.py:70`

Attributes:
 - `feature.id`
 - `organisation.id`
 - `project.id`
 - `resource.type`

### `gitlab.webhook.deregistered`

Logged at `info` from:
 - `api/integrations/gitlab/services/webhooks.py:157`

Attributes:
 - `gitlab.hook.id`
 - `gitlab.project.id`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.deregistration_failed`

Logged at `warning` from:
 - `api/integrations/gitlab/services/webhooks.py:150`

Attributes:
 - `exc_info`
 - `gitlab.hook.id`
 - `gitlab.project.id`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.processed`

Logged at `info` from:
 - `api/integrations/gitlab/views/webhook.py:35`

Attributes:
 - `action`
 - `object_kind`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.registered`

Logged at `info` from:
 - `api/integrations/gitlab/services/webhooks.py:110`

Attributes:
 - `gitlab.hook.id`
 - `gitlab.project.id`
 - `gitlab.project.path`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.registration_failed`

Logged at `error` from:
 - `api/integrations/gitlab/services/webhooks.py:95`

Attributes:
 - `exc_info`
 - `gitlab.project.path`
 - `organisation.id`
 - `project.id`

### `launch_darkly.import_failed`

Logged at `exception` from:
 - `api/integrations/launch_darkly/tasks.py:36`

Attributes:
 - `import_request_id`
 - `ld_project_key`
 - `organisation_id`
 - `project_id`

### `launch_darkly.import_rate_limit_reached`

Logged at `warning` from:
 - `api/integrations/launch_darkly/tasks.py:26`

Attributes:
 - `error_message`
 - `import_request_id`
 - `ld_project_key`
 - `organisation_id`
 - `project_id`
 - `retry_at`

### `mcp.tool.called`

Logged at `info` from:
 - `api/telemetry/middleware.py:38`
 - `api/telemetry/middleware.py:40`

Attributes:
 - `organisation.id`

### `platform_hub.no_analytics_database_configured`

Logged at `warning` from:
 - `api/platform_hub/services.py:116`
 - `api/platform_hub/services.py:206`
 - `api/platform_hub/services.py:428`

Attributes:

### `segment_membership.compute.segment.skipped`

Logged at `error` from:
 - `api/segment_membership/services.py:149`

Attributes:
 - `project.id`
 - `reason`
 - `segment.id`

### `segment_membership.members.segment.skipped`

Logged at `error` from:
 - `api/segment_membership/services.py:215`

Attributes:
 - `reason`
 - `segment.id`

### `segment_membership.refresh.project.completed`

Logged at `info` from:
 - `api/segment_membership/tasks.py:266`

Attributes:
 - `membership_counts.count`
 - `project.id`
 - `stale_counts.count`

### `segment_membership.refresh.project.failed`

Logged at `exception` from:
 - `api/segment_membership/tasks.py:239`

Attributes:
 - `project.id`

### `segment_membership.refresh.project.skipped`

Logged at `info` from:
 - `api/segment_membership/tasks.py:206`
 - `api/segment_membership/tasks.py:218`

Attributes:
 - `project.id`
 - `reason`
 - `stale_counts.count`

### `segment_membership.seed.environment.completed`

Logged at `info` from:
 - `api/segment_membership/tasks.py:121`

Attributes:
 - `environment.id`
 - `organisation.id`
 - `project.id`
 - `rows.count`

### `segment_membership.seed.environment.failed`

Logged at `exception` from:
 - `api/segment_membership/tasks.py:114`

Attributes:
 - `environment.id`
 - `organisation.id`
 - `project.id`

### `segment_membership.seed.skipped`

Logged at `warning` from:
 - `api/segment_membership/tasks.py:67`
 - `api/segment_membership/tasks.py:72`
 - `api/segment_membership/tasks.py:77`

Attributes:
 - `organisation.id`
 - `reason`

### `segments.serializers.segment_revision_created`

Logged at `info` from:
 - `api/segments/serializers.py:158`

Attributes:
 - `revision_id`
 - `segment_id`

### `sentry_change_tracking.integration_error`

Logged at `warning` from:
 - `api/integrations/sentry/change_tracking.py:109`

Attributes:
 - `feature_name`
 - `sentry_action`
 - `sentry_response_body`
 - `sentry_response_status`

### `sentry_change_tracking.request_failure`

Logged at `warning` from:
 - `api/integrations/sentry/change_tracking.py:99`

Attributes:
 - `error`
 - `feature_name`
 - `sentry_action`

### `sentry_change_tracking.sending`

Logged at `debug` from:
 - `api/integrations/sentry/change_tracking.py:84`

Attributes:
 - `feature_name`
 - `headers`
 - `payload`
 - `sentry_action`
 - `url`

### `sentry_change_tracking.success`

Logged at `info` from:
 - `api/integrations/sentry/change_tracking.py:106`

Attributes:
 - `feature_name`
 - `sentry_action`

### `usage_reporting.run.skipped`

Logged at `debug` from:
 - `api/organisations/usage_reporting/services.py:60`
 - `api/organisations/usage_reporting/services.py:63`

Attributes:
 - `reason`

### `usage_reporting.snapshot.errored`

Logged at `exception` from:
 - `api/organisations/usage_reporting/services.py:75`

Attributes:

### `usage_reporting.snapshot.push_failed`

Logged at `warning` from:
 - `api/organisations/usage_reporting/services.py:55`

Attributes:
 - `status_code`

### `usage_reporting.snapshot.pushed`

Logged at `info` from:
 - `api/organisations/usage_reporting/services.py:53`

Attributes:
 - `status_code`

### `warehouse.connection.connected`

Logged at `info` from:
 - `api/experimentation/services.py:878`

Attributes:
 - `environment.id`
 - `organisation.id`

### `warehouse.connection.test_event_sent`

Logged at `info` from:
 - `api/experimentation/services.py:790`

Attributes:
 - `environment.id`
 - `organisation.id`

### `warehouse.connection.verification_failed`

Logged at `warning` from:
 - `api/experimentation/services.py:854`

Attributes:
 - `environment.id`
 - `exc_info`
 - `organisation.id`

### `warehouse.connection.verification_succeeded`

Logged at `info` from:
 - `api/experimentation/services.py:863`

Attributes:
 - `environment.id`
 - `organisation.id`

### `warehouse.srm.overallocated`

Logged at `error` from:
 - `api/experimentation/services.py:412`

Attributes:
 - `environment.id`
 - `experiment.id`
 - `feature.id`

### `warehouse.srm.unkeyed_variant`

Logged at `error` from:
 - `api/experimentation/services.py:398`

Attributes:
 - `environment.id`
 - `experiment.id`
 - `feature.id`

### `workflows.change_request.committed`

Logged at `info` from:
 - `api/core/workflows_services.py:39`

Attributes:
 - `environment.id`
 - `feature_states.count`
 - `organisation.id`

### `workflows.missing_live_segment`

Logged at `warning` from:
 - `api/core/workflows_services.py:114`

Attributes:
 - `draft_segment`

### `workflows.segment_revision_created`

Logged at `info` from:
 - `api/core/workflows_services.py:119`

Attributes:
 - `revision_id`
 - `segment_id`

