
### `app_analytics.no_analytics_database_configured`

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

### `dynamodb.environment_document_compressed`

Logged at `info` from:
 - `api/environments/dynamodb/wrappers/environment_wrapper.py:92`

Attributes:
 - `environment_api_key`
 - `environment_id`

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

### `gitlab.feature.tagged`

Logged at `info` from:
 - `api/integrations/gitlab/services/tagging.py:89`

Attributes:
 - `action`
 - `feature.id`
 - `object_kind`
 - `organisation.id`
 - `project.id`
 - `tag.label`

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
 - `api/integrations/gitlab/tasks.py:170`

Attributes:
 - `feature.id`
 - `gitlab_project.path`
 - `project.id`
 - `resource.iid`
 - `resource.type`

### `gitlab.label.removed`

Logged at `info` from:
 - `api/integrations/gitlab/tasks.py:168`

Attributes:
 - `feature.id`
 - `gitlab_project.path`
 - `project.id`
 - `resource.iid`
 - `resource.type`

### `gitlab.resource.linked`

Logged at `info` from:
 - `api/integrations/vcs/services.py:28`

Attributes:
 - `feature.id`
 - `organisation.id`
 - `project.id`
 - `resource.type`

### `gitlab.resource.unlinked`

Logged at `info` from:
 - `api/integrations/vcs/services.py:63`

Attributes:
 - `feature.id`
 - `organisation.id`
 - `project.id`
 - `resource.type`

### `gitlab.webhook.deregistered`

Logged at `info` from:
 - `api/integrations/gitlab/services/webhooks.py:152`

Attributes:
 - `gitlab.hook.id`
 - `gitlab.project.id`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.deregistration_failed`

Logged at `warning` from:
 - `api/integrations/gitlab/services/webhooks.py:145`

Attributes:
 - `exc_info`
 - `gitlab.hook.id`
 - `gitlab.project.id`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.registered`

Logged at `info` from:
 - `api/integrations/gitlab/services/webhooks.py:105`

Attributes:
 - `gitlab.hook.id`
 - `gitlab.project.id`
 - `gitlab.project.path`
 - `organisation.id`
 - `project.id`

### `gitlab.webhook.registration_failed`

Logged at `error` from:
 - `api/integrations/gitlab/services/webhooks.py:90`

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

### `platform_hub.no_analytics_database_configured`

Logged at `warning` from:
 - `api/platform_hub/services.py:116`
 - `api/platform_hub/services.py:206`
 - `api/platform_hub/services.py:428`

Attributes:

### `segments.serializers.segment_revision_created`

Logged at `info` from:
 - `api/segments/serializers.py:142`

Attributes:
 - `revision_id`
 - `segment_id`

### `sentry_change_tracking.integration_error`

Logged at `warning` from:
 - `api/integrations/sentry/change_tracking.py:112`

Attributes:
 - `feature_name`
 - `sentry_action`
 - `sentry_response_body`
 - `sentry_response_status`

### `sentry_change_tracking.request_failure`

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

