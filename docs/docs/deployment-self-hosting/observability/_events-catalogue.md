$schema: https://spec.openapis.org/oas/3.1/dialect/base
openapi: 3.1.0
info:
  title: Flagsmith API
  version: v1
  description: Flagsmith's Core and SDK APIs. Check out <a href='https://docs.flagsmith.com'>Flagsmith
    documentation</a>.
  contact:
    email: support@flagsmith.com
  license:
    name: BSD License
    identifier: BSD-3-Clause
paths:
  /api/experiments/environments/{environment_key}/delete-segment-override/:
    post:
      operationId: api_experiments_environments_delete_segment_override_create
      description: "\n    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.\n\
        \n    Deletes a segment override for a feature in the given environment.\n\
        \n    **Feature Identification:**\n    - Use `feature.name` OR `feature.id`\
        \ (mutually exclusive)\n    - Feature must belong to the environment's project\n\
        \n    **Segment Identification:**\n    - Use `segment.id` (required)\n\n \
        \   The segment override must exist for the given feature/environment combination.\n\
        \    Returns 400 if the segment override does not exist.\n    "
      summary: Delete segment override
      parameters:
      - in: path
        name: environment_key
        schema:
          type: string
        description: The environment API key
        required: true
      tags:
      - experimental
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DeleteSegmentOverride'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/DeleteSegmentOverride'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/DeleteSegmentOverride'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/experiments/environments/{environment_key}/update-flag-v1/:
    post:
      operationId: api_experiments_environments_update_flag_v1_create
      description: "\n    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.\n\
        \n    Updates a single feature state within an environment. You can update\
        \ either:\n    - The environment default state (when no segment is specified)\n\
        \    - A specific segment override (when segment.id is provided)\n\n    **Feature\
        \ Identification:**\n    - Use `feature.name` OR `feature.id` (mutually exclusive)\n\
        \n    **Value Format:**\n    - The `value` field is always a string representation\n\
        \    - The `type` field tells the server how to parse it\n    - Available\
        \ types: integer, string, boolean\n    - Examples:\n      - `{\"type\": \"\
        integer\", \"value\": \"42\"}`\n      - `{\"type\": \"boolean\", \"value\"\
        : \"true\"}`\n      - `{\"type\": \"string\", \"value\": \"hello\"}`\n\n \
        \   **Segment Priority:**\n    - Optional `segment.priority` field controls\
        \ ordering\n    - If field value is null or the field is omitted, lowest priority\
        \ is assumed\n    "
      summary: Update single feature state
      parameters:
      - in: path
        name: environment_key
        schema:
          type: string
        description: The environment API key
        required: true
      tags:
      - experimental
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateFlag'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UpdateFlag'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UpdateFlag'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/experiments/environments/{environment_key}/update-flag-v2/:
    post:
      operationId: api_experiments_environments_update_flag_v2_create
      description: "\n    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.\n\
        \n    Updates multiple feature states in a single request. This endpoint allows\n\
        \    you to configure an entire feature (environment default + all segment\
        \ overrides)\n    in one operation.\n\n    **What You Can Update:**\n    -\
        \ Environment default state (required)\n    - Multiple segment overrides (optional)\n\
        \    - Priority ordering for each segment\n\n    **Feature Identification:**\n\
        \    - Use `feature.name` OR `feature.id` (mutually exclusive)\n\n    **Value\
        \ Format:**\n    - The `value` field is always a string representation\n \
        \   - The `type` field tells the server how to parse it\n    - Available types:\
        \ integer, string, boolean\n    - Examples:\n      - `{\"type\": \"string\"\
        , \"value\": \"production\"}`\n      - `{\"type\": \"integer\", \"value\"\
        : \"100\"}`\n      - `{\"type\": \"boolean\", \"value\": \"false\"}`\n\n \
        \   **Segment Overrides:**\n    - Provide array of segment override configurations\n\
        \    - Each override must specify: segment_id, enabled, value\n    - Optional\
        \ priority field controls ordering\n    - Duplicate segment_id values are\
        \ not allowed\n\n    "
      summary: Update multiple feature states
      parameters:
      - in: path
        name: environment_key
        schema:
          type: string
        description: The environment API key
        required: true
      tags:
      - experimental
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateFlagV2'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UpdateFlagV2'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UpdateFlagV2'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/admin/dashboard/integrations/:
    get:
      operationId: api_v1_admin_dashboard_integrations_retrieve
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/admin/dashboard/organisations/:
    get:
      operationId: api_v1_admin_dashboard_organisations_retrieve
      tags:
      - Admin dashboard
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/admin/dashboard/release-pipelines/:
    get:
      operationId: api_v1_admin_dashboard_release_pipelines_retrieve
      tags:
      - Admin dashboard
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/admin/dashboard/stale-flags/:
    get:
      operationId: api_v1_admin_dashboard_stale_flags_retrieve
      tags:
      - Admin dashboard
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/admin/dashboard/summary/:
    get:
      operationId: api_v1_admin_dashboard_summary_retrieve
      tags:
      - Admin dashboard
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/admin/dashboard/usage-trends/:
    get:
      operationId: api_v1_admin_dashboard_usage_trends_retrieve
      tags:
      - Admin dashboard
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/analytics/flags/:
    post:
      operationId: api_v1_analytics_flags_create
      description: Class to handle flag analytics events
      tags:
      - Analytics
      security:
      - Environment API Key: []
      responses:
        '201':
          description: No response body
  /api/v1/analytics/telemetry/:
    post:
      operationId: api_v1_analytics_telemetry_create
      description: |-
        Class to handle telemetry events from self hosted APIs so we can aggregate and track
        self hosted installation data
      tags:
      - Analytics
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Telemetry'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Telemetry'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Telemetry'
        required: true
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Telemetry'
          description: ''
  /api/v1/audit/:
    get:
      operationId: api_v1_audit_list
      parameters:
      - in: query
        name: environments
        schema:
          type: array
          items:
            type: integer
            minimum: 0
      - in: query
        name: is_system_event
        schema:
          type:
          - boolean
          - 'null'
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      - in: query
        name: project
        schema:
          type: integer
      - in: query
        name: search
        schema:
          type: string
          maxLength: 256
          minLength: 1
      tags:
      - Audit
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedAuditLogListList'
          description: ''
  /api/v1/audit/{id}/:
    get:
      operationId: api_v1_audit_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this audit log.
        required: true
      tags:
      - Audit
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuditLogRetrieve'
          description: ''
  /api/v1/auth/{method}/activate/:
    post:
      operationId: api_v1_auth_activate_create
      parameters:
      - in: path
        name: method
        schema:
          type: string
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/auth/{method}/activate/confirm/:
    post:
      operationId: api_v1_auth_activate_confirm_create
      parameters:
      - in: path
        name: method
        schema:
          type: string
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/auth/{method}/deactivate/:
    post:
      operationId: api_v1_auth_deactivate_create
      parameters:
      - in: path
        name: method
        schema:
          type: string
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/auth/login/:
    post:
      operationId: api_v1_auth_login_create
      description: Class to handle throttling for login requests
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/TokenCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/TokenCreate'
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenCreate'
          description: ''
  /api/v1/auth/login/code/:
    post:
      operationId: api_v1_auth_login_code_create
      description: Override class to add throttling
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/TokenCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/TokenCreate'
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenCreate'
          description: ''
  /api/v1/auth/logout/:
    post:
      operationId: api_v1_auth_logout_create
      description: Use this endpoint to logout user (remove user authentication token).
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/auth/mfa/user-active-methods/:
    get:
      operationId: api_v1_auth_mfa_user_active_methods_retrieve
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/auth/oauth/github/:
    post:
      operationId: api_v1_auth_oauth_github_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GithubLogin'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GithubLogin'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GithubLogin'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomToken'
          description: ''
        '502':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: ''
  /api/v1/auth/oauth/google/:
    post:
      operationId: api_v1_auth_oauth_google_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GoogleLogin'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GoogleLogin'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GoogleLogin'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomToken'
          description: ''
        '502':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: ''
  /api/v1/auth/token/:
    delete:
      operationId: api_v1_auth_token_destroy
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/auth/users/:
    get:
      operationId: api_v1_auth_users_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedUserList'
          description: ''
    post:
      operationId: api_v1_auth_users_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomUserCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CustomUserCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CustomUserCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomUserCreate'
          description: ''
  /api/v1/auth/users/{id}/:
    get:
      operationId: api_v1_auth_users_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this Feature flag admin user.
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
          description: ''
    put:
      operationId: api_v1_auth_users_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this Feature flag admin user.
        required: true
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/User'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/User'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
          description: ''
    patch:
      operationId: api_v1_auth_users_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this Feature flag admin user.
        required: true
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedUser'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedUser'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedUser'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
          description: ''
    delete:
      operationId: api_v1_auth_users_destroy
      parameters:
      - in: query
        name: current_password
        schema:
          type:
          - string
          - 'null'
      - in: query
        name: delete_orphan_organisations
        schema:
          type: boolean
          default: false
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this Feature flag admin user.
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/auth/users/activation/:
    post:
      operationId: api_v1_auth_users_activation_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Activation'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Activation'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Activation'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Activation'
          description: ''
  /api/v1/auth/users/me/:
    get:
      operationId: api_v1_auth_users_me_retrieve
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomCurrentUser'
          description: ''
    put:
      operationId: api_v1_auth_users_me_update
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomCurrentUser'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CustomCurrentUser'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CustomCurrentUser'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomCurrentUser'
          description: ''
    patch:
      operationId: api_v1_auth_users_me_partial_update
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCustomCurrentUser'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCustomCurrentUser'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCustomCurrentUser'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomCurrentUser'
          description: ''
    delete:
      operationId: api_v1_auth_users_me_destroy
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/auth/users/me/onboarding/:
    patch:
      operationId: api_v1_auth_users_me_onboarding_partial_update
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedUser'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedUser'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedUser'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
          description: ''
  /api/v1/auth/users/resend_activation/:
    post:
      operationId: api_v1_auth_users_resend_activation_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SendEmailReset'
          description: ''
  /api/v1/auth/users/reset_email/:
    post:
      operationId: api_v1_auth_users_reset_email_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SendEmailReset'
          description: ''
  /api/v1/auth/users/reset_email_confirm/:
    post:
      operationId: api_v1_auth_users_reset_email_confirm_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UsernameResetConfirm'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UsernameResetConfirm'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UsernameResetConfirm'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UsernameResetConfirm'
          description: ''
  /api/v1/auth/users/reset_password/:
    post:
      operationId: api_v1_auth_users_reset_password_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SendEmailReset'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SendEmailReset'
          description: ''
  /api/v1/auth/users/reset_password_confirm/:
    post:
      operationId: api_v1_auth_users_reset_password_confirm_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PasswordResetConfirmRetype'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PasswordResetConfirmRetype'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PasswordResetConfirmRetype'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PasswordResetConfirmRetype'
          description: ''
  /api/v1/auth/users/set_email/:
    post:
      operationId: api_v1_auth_users_set_email_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SetUsername'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SetUsername'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SetUsername'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SetUsername'
          description: ''
  /api/v1/auth/users/set_password/:
    post:
      operationId: api_v1_auth_users_set_password_create
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SetPasswordRetype'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SetPasswordRetype'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SetPasswordRetype'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SetPasswordRetype'
          description: ''
  /api/v1/cb-webhook/:
    post:
      operationId: api_v1_cb_webhook_create
      description: |-
        Endpoint to handle webhooks from chargebee.

        Payment failure and payment succeeded webhooks are filtered out and processed
        to determine which of our subscriptions are in a dunning state.

        The remaining webhooks are processed if they have subscription data:

         - If subscription is active, check to see if plan has changed and update if so. Always update cancellation date to
           None to ensure that if a subscription is reactivated, it is updated on our end.

         - If subscription is cancelled or not renewing, update subscription on our end to include cancellation date and
           send alert to admin users.
      tags:
      - Webhooks
      security:
      - basicAuth: []
      responses:
        '200':
          description: No response body
  /api/v1/environment-document/:
    get:
      operationId: sdk_v1_environment_document
      description: |-
        Retrieve the environment document.
        Used by SDKs in local evaluation mode, and Edge Proxy.
      tags:
      - sdk
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/V1EnvironmentDocumentResponse'
          description: ''
  /api/v1/environment-feature-versions/{id}/:
    get:
      operationId: api_v1_environment_feature_versions_retrieve
      description: |-
        This is an additional endpoint to retrieve a specific version without needing
        to provide the environment or feature as part of the URL.
      parameters:
      - in: path
        name: id
        schema:
          type: string
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentFeatureVersionRetrieve'
          description: ''
  /api/v1/environments/:
    get:
      operationId: api_v1_environments_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: query
        name: project
        schema:
          type: integer
        description: ID of the project to filter by.
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedEnvironmentSerializerWithMetadataList'
          description: ''
      x-gram:
        name: list_environments
        description: Lists all environments the user has access to
    post:
      operationId: api_v1_environments_create
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateEnvironment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateEnvironment'
          description: ''
  /api/v1/environments/{api_key}/:
    get:
      operationId: api_v1_environments_retrieve
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentRetrieveSerializerWithMetadata'
          description: ''
    put:
      operationId: api_v1_environments_update
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UpdateEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UpdateEnvironment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateEnvironment'
          description: ''
    patch:
      operationId: api_v1_environments_partial_update
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedUpdateEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedUpdateEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedUpdateEnvironment'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateEnvironment'
          description: ''
    delete:
      operationId: api_v1_environments_destroy
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{api_key}/clone/:
    post:
      operationId: api_v1_environments_clone_create
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CloneEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CloneEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CloneEnvironment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CloneEnvironment'
          description: ''
  /api/v1/environments/{api_key}/delete-traits/:
    post:
      operationId: api_v1_environments_delete_traits_create
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DeleteAllTraitKeys'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/DeleteAllTraitKeys'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/DeleteAllTraitKeys'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeleteAllTraitKeys'
          description: ''
  /api/v1/environments/{api_key}/disable-v2-versioning/:
    post:
      operationId: api_v1_environments_disable_v2_versioning_create
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '202':
          description: No response body
  /api/v1/environments/{api_key}/document/:
    get:
      operationId: api_v1_environments_document_retrieve
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/V1EnvironmentDocumentResponse'
          description: ''
  /api/v1/environments/{api_key}/enable-v2-versioning/:
    post:
      operationId: api_v1_environments_enable_v2_versioning_create
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '202':
          description: No response body
  /api/v1/environments/{api_key}/my-permissions/:
    get:
      operationId: api_v1_environments_my_permissions_retrieve
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserObjectPermissions'
          description: ''
  /api/v1/environments/{api_key}/trait-keys/:
    get:
      operationId: api_v1_environments_trait_keys_retrieve
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TraitKeys'
          description: ''
  /api/v1/environments/{api_key}/user-detailed-permissions/{user_id}/:
    get:
      operationId: api_v1_environments_user_detailed_permissions_retrieve
      parameters:
      - in: path
        name: api_key
        schema:
          type: string
        required: true
      - in: path
        name: user_id
        schema:
          type: string
          pattern: ^\d+$
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserDetailedPermissions'
          description: ''
  /api/v1/environments/{environment_api_key}/api-keys/:
    get:
      operationId: api_v1_environments_api_keys_list
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/EnvironmentAPIKey'
          description: ''
    post:
      operationId: api_v1_environments_api_keys_create
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnvironmentAPIKey'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EnvironmentAPIKey'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EnvironmentAPIKey'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentAPIKey'
          description: ''
  /api/v1/environments/{environment_api_key}/api-keys/{id}/:
    put:
      operationId: api_v1_environments_api_keys_update
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this environment api key.
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnvironmentAPIKey'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EnvironmentAPIKey'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EnvironmentAPIKey'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentAPIKey'
          description: ''
    patch:
      operationId: api_v1_environments_api_keys_partial_update
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this environment api key.
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedEnvironmentAPIKey'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedEnvironmentAPIKey'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedEnvironmentAPIKey'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentAPIKey'
          description: ''
    delete:
      operationId: api_v1_environments_api_keys_destroy
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this environment api key.
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/edge-identities/:
    get:
      operationId: api_v1_environments_edge_identities_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - name: last_evaluated_key
        in: query
        description: Used as the starting point for the page
        required: false
        schema:
          type: string
      - name: page_size
        in: query
        description: Number of results to return per page.
        required: false
        schema:
          type: integer
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedEdgeIdentityList'
          description: ''
    post:
      operationId: api_v1_environments_edge_identities_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentity'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentity'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentity'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentity'
          description: ''
  /api/v1/environments/{environment_api_key}/edge-identities/{edge_identity_identity_uuid}/edge-featurestates/:
    get:
      operationId: api_v1_environments_edge_identities_edge_featurestates_list
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: query
        name: feature
        schema:
          type: integer
        description: ID of the feature to filter by
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/EdgeIdentityFeatureState'
          description: ''
    post:
      operationId: api_v1_environments_edge_identities_edge_featurestates_create
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentityFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentityFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentityFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityFeatureState'
          description: ''
  ? /api/v1/environments/{environment_api_key}/edge-identities/{edge_identity_identity_uuid}/edge-featurestates/{featurestate_uuid}/
  : get:
      operationId: api_v1_environments_edge_identities_edge_featurestates_retrieve
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: featurestate_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityFeatureState'
          description: ''
    put:
      operationId: api_v1_environments_edge_identities_edge_featurestates_update
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: featurestate_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentityFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentityFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentityFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityFeatureState'
          description: ''
    delete:
      operationId: api_v1_environments_edge_identities_edge_featurestates_destroy
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: featurestate_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/edge-identities/{edge_identity_identity_uuid}/edge-featurestates/all/:
    get:
      operationId: api_v1_environments_edge_identities_edge_featurestates_all_list
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/IdentityAllFeatureStates'
          description: ''
  ? /api/v1/environments/{environment_api_key}/edge-identities/{edge_identity_identity_uuid}/edge-featurestates/clone-from-given-identity/
  : post:
      operationId: api_v1_environments_edge_identities_edge_featurestates_clone_from_given_identity_create
      description: Clone feature states from a given source identity.
      parameters:
      - in: path
        name: edge_identity_identity_uuid
        schema:
          type: string
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentitySourceIdentityRequest'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentitySourceIdentityRequest'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentitySourceIdentityRequest'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/IdentityAllFeatureStates'
          description: ''
  /api/v1/environments/{environment_api_key}/edge-identities/{identity_uuid}/:
    get:
      operationId: api_v1_environments_edge_identities_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentity'
          description: ''
    put:
      operationId: api_v1_environments_edge_identities_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentityUpdate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentityUpdate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentityUpdate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityUpdate'
          description: ''
    patch:
      operationId: api_v1_environments_edge_identities_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedEdgeIdentityUpdate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedEdgeIdentityUpdate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedEdgeIdentityUpdate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityUpdate'
          description: ''
    delete:
      operationId: api_v1_environments_edge_identities_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/edge-identities/{identity_uuid}/list-traits/:
    get:
      operationId: api_v1_environments_edge_identities_list_traits_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_uuid
        schema:
          type: string
        required: true
      - name: last_evaluated_key
        in: query
        description: Used as the starting point for the page
        required: false
        schema:
          type: string
      - name: page_size
        in: query
        description: Number of results to return per page.
        required: false
        schema:
          type: integer
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedEdgeIdentityTraitsList'
          description: ''
  /api/v1/environments/{environment_api_key}/edge-identities/{identity_uuid}/update-traits/:
    put:
      operationId: api_v1_environments_edge_identities_update_traits_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_uuid
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentityTraits'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentityTraits'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentityTraits'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityTraits'
          description: ''
  /api/v1/environments/{environment_api_key}/edge-identity-overrides:
    get:
      operationId: api_v1_environments_edge_identity_overrides_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: query
        name: feature
        schema:
          type: integer
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetEdgeIdentityOverrides'
          description: ''
  /api/v1/environments/{environment_api_key}/experiments/results/:
    get:
      operationId: api_v1_environments_experiments_results_retrieve
      description: |-
        Get experiment results for a feature.

        Returns conversion rates and statistical significance for each variant
        of a feature flag experiment.

        Trait naming convention:
        - Variant tracking: `exp_{feature}_variant` (string value)
        - Conversion tracking: `exp_{feature}_converted` (boolean value)
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: query
        name: feature
        schema:
          type: string
        description: Feature name to analyse
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExperimentResults'
          description: ''
  /api/v1/environments/{environment_api_key}/features/{feature_pk}/create-segment-override/:
    post:
      operationId: api_v1_environments_features_create_segment_override_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureState'
          description: ''
      x-gram:
        name: create_segment_override
        description: 'Creates a segment override for a feature in an environment in
          a single call, setting both the segment binding and its value. Use this
          tool for environments without v2 feature versioning (use_v2_feature_versioning:
          false).'
  /api/v1/environments/{environment_api_key}/featurestates/:
    get:
      operationId: api_v1_environments_featurestates_list
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: query
        name: anyIdentity
        schema:
          type: string
        description: Pass any value to get results that have an identity override.
          Do not pass for default behaviour.
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: query
        name: feature
        schema:
          type: integer
        description: ID of the feature to filter by.
      - in: query
        name: feature_name
        schema:
          type: string
        description: Name of the feature to filter by.
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureStateSerializerWithIdentityList'
          description: ''
    post:
      operationId: api_v1_environments_featurestates_create
      description: |-
        DEPRECATED: please use `/features/featurestates/` instead.
        Override create method to add environment and identity (if present) from URL parameters.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerBasic'
          description: ''
  /api/v1/environments/{environment_api_key}/featurestates/{id}/:
    get:
      operationId: api_v1_environments_featurestates_retrieve
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerBasic'
          description: ''
    put:
      operationId: api_v1_environments_featurestates_update
      description: |-
        Override update method to always assume update request is partial and create / update
        feature state value.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerBasic'
          description: ''
      x-gram:
        name: update_environment_feature_state
        description: 'Updates a feature state in an environment, including enabled
          status and value. Use this tool for environments without v2 feature versioning
          (use_v2_feature_versioning: false).'
    patch:
      operationId: api_v1_environments_featurestates_partial_update
      description: Override partial_update as overridden update method assumes partial
        True for all requests.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedFeatureStateSerializerCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedFeatureStateSerializerCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedFeatureStateSerializerCreate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerCreate'
          description: ''
    delete:
      operationId: api_v1_environments_featurestates_destroy
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/identities/:
    get:
      operationId: api_v1_environments_identities_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedIdentityList'
          description: ''
    post:
      operationId: api_v1_environments_identities_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Identity'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Identity'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Identity'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Identity'
          description: ''
  /api/v1/environments/{environment_api_key}/identities/{identity_pk}/featurestates/:
    get:
      operationId: api_v1_environments_identities_featurestates_list
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: query
        name: anyIdentity
        schema:
          type: string
        description: Pass any value to get results that have an identity override.
          Do not pass for default behaviour.
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: query
        name: feature
        schema:
          type: integer
        description: ID of the feature to filter by.
      - in: query
        name: feature_name
        schema:
          type: string
        description: Name of the feature to filter by.
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureStateSerializerWithIdentityList'
          description: ''
    post:
      operationId: api_v1_environments_identities_featurestates_create
      description: |-
        DEPRECATED: please use `/features/featurestates/` instead.
        Override create method to add environment and identity (if present) from URL parameters.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerBasic'
          description: ''
  /api/v1/environments/{environment_api_key}/identities/{identity_pk}/featurestates/{id}/:
    get:
      operationId: api_v1_environments_identities_featurestates_retrieve
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerBasic'
          description: ''
    put:
      operationId: api_v1_environments_identities_featurestates_update
      description: |-
        Override update method to always assume update request is partial and create / update
        feature state value.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureStateSerializerBasic'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerBasic'
          description: ''
    patch:
      operationId: api_v1_environments_identities_featurestates_partial_update
      description: Override partial_update as overridden update method assumes partial
        True for all requests.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedFeatureStateSerializerCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedFeatureStateSerializerCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedFeatureStateSerializerCreate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerCreate'
          description: ''
    delete:
      operationId: api_v1_environments_identities_featurestates_destroy
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/identities/{identity_pk}/featurestates/all/:
    get:
      operationId: api_v1_environments_identities_featurestates_all_retrieve
      description: |-
        View set to manage feature states. Nested beneath environments and environments + identities
        to allow for filtering on both.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureStateSerializerCreate'
          description: ''
  /api/v1/environments/{environment_api_key}/identities/{identity_pk}/featurestates/clone-from-given-identity/:
    post:
      operationId: api_v1_environments_identities_featurestates_clone_from_given_identity_create
      description: Clone feature states from a given source identity.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/IdentitySourceIdentityRequest'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/IdentitySourceIdentityRequest'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/IdentitySourceIdentityRequest'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedIdentityAllFeatureStatesList'
          description: ''
  /api/v1/environments/{environment_api_key}/identities/{identity_pk}/traits/:
    get:
      operationId: api_v1_environments_identities_traits_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedTraitList'
          description: ''
    post:
      operationId: api_v1_environments_identities_traits_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: identity_pk
        schema:
          type: integer
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Trait'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Trait'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Trait'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trait'
          description: ''
  /api/v1/environments/{environment_api_key}/identities/{identity_pk}/traits/{id}/:
    get:
      operationId: api_v1_environments_identities_traits_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this trait.
        required: true
      - in: path
        name: identity_pk
        schema:
          type: integer
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trait'
          description: ''
    put:
      operationId: api_v1_environments_identities_traits_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this trait.
        required: true
      - in: path
        name: identity_pk
        schema:
          type: integer
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Trait'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Trait'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Trait'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trait'
          description: ''
    patch:
      operationId: api_v1_environments_identities_traits_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this trait.
        required: true
      - in: path
        name: identity_pk
        schema:
          type: integer
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedTrait'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedTrait'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedTrait'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trait'
          description: ''
    delete:
      operationId: api_v1_environments_identities_traits_destroy
      parameters:
      - in: query
        name: deleteAllMatchingTraits
        schema:
          type: boolean
        description: Deletes all traits in this environment matching the key of the
          deleted trait
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this trait.
        required: true
      - in: path
        name: identity_pk
        schema:
          type: integer
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/identities/{id}/:
    get:
      operationId: api_v1_environments_identities_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this identity.
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Identity'
          description: ''
    put:
      operationId: api_v1_environments_identities_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this identity.
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Identity'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Identity'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Identity'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Identity'
          description: ''
    patch:
      operationId: api_v1_environments_identities_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this identity.
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedIdentity'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedIdentity'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedIdentity'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Identity'
          description: ''
    delete:
      operationId: api_v1_environments_identities_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this identity.
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/amplitude/:
    get:
      operationId: api_v1_environments_integrations_amplitude_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AmplitudeConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_amplitude_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AmplitudeConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/AmplitudeConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/AmplitudeConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AmplitudeConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/amplitude/{id}/:
    get:
      operationId: api_v1_environments_integrations_amplitude_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this amplitude configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AmplitudeConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_amplitude_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this amplitude configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AmplitudeConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/AmplitudeConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/AmplitudeConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AmplitudeConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_amplitude_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this amplitude configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedAmplitudeConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedAmplitudeConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedAmplitudeConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AmplitudeConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_amplitude_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this amplitude configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/dynatrace/:
    get:
      operationId: api_v1_environments_integrations_dynatrace_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/DynatraceConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_dynatrace_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DynatraceConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/DynatraceConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/DynatraceConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DynatraceConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/dynatrace/{id}/:
    get:
      operationId: api_v1_environments_integrations_dynatrace_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this dynatrace configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DynatraceConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_dynatrace_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this dynatrace configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DynatraceConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/DynatraceConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/DynatraceConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DynatraceConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_dynatrace_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this dynatrace configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedDynatraceConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedDynatraceConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedDynatraceConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DynatraceConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_dynatrace_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this dynatrace configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/grafana/:
    get:
      operationId: api_v1_environments_integrations_grafana_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_grafana_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/grafana/{id}/:
    get:
      operationId: api_v1_environments_integrations_grafana_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_grafana_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_grafana_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaProjectConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaProjectConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaProjectConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_grafana_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/heap/:
    get:
      operationId: api_v1_environments_integrations_heap_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/HeapConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_heap_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/HeapConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/HeapConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/HeapConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HeapConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/heap/{id}/:
    get:
      operationId: api_v1_environments_integrations_heap_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this heap configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HeapConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_heap_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this heap configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/HeapConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/HeapConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/HeapConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HeapConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_heap_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this heap configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedHeapConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedHeapConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedHeapConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HeapConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_heap_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this heap configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/mixpanel/:
    get:
      operationId: api_v1_environments_integrations_mixpanel_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/MixpanelConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_mixpanel_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MixpanelConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MixpanelConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MixpanelConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MixpanelConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/mixpanel/{id}/:
    get:
      operationId: api_v1_environments_integrations_mixpanel_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this mixpanel configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MixpanelConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_mixpanel_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this mixpanel configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MixpanelConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MixpanelConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MixpanelConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MixpanelConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_mixpanel_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this mixpanel configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedMixpanelConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedMixpanelConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedMixpanelConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MixpanelConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_mixpanel_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this mixpanel configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/rudderstack/:
    get:
      operationId: api_v1_environments_integrations_rudderstack_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/RudderstackConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_rudderstack_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RudderstackConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/RudderstackConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/RudderstackConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RudderstackConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/rudderstack/{id}/:
    get:
      operationId: api_v1_environments_integrations_rudderstack_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this rudderstack configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RudderstackConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_rudderstack_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this rudderstack configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RudderstackConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/RudderstackConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/RudderstackConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RudderstackConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_rudderstack_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this rudderstack configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedRudderstackConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedRudderstackConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedRudderstackConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RudderstackConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_rudderstack_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this rudderstack configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/segment/:
    get:
      operationId: api_v1_environments_integrations_segment_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/SegmentConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_segment_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SegmentConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SegmentConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SegmentConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SegmentConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/segment/{id}/:
    get:
      operationId: api_v1_environments_integrations_segment_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SegmentConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_segment_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SegmentConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SegmentConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SegmentConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SegmentConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_segment_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedSegmentConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedSegmentConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedSegmentConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SegmentConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_segment_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/sentry/:
    get:
      operationId: api_v1_environments_integrations_sentry_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_sentry_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/sentry/{id}/:
    get:
      operationId: api_v1_environments_integrations_sentry_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this sentry change tracking
          configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_sentry_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this sentry change tracking
          configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_sentry_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this sentry change tracking
          configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedSentryChangeTrackingConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedSentryChangeTrackingConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedSentryChangeTrackingConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SentryChangeTrackingConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_sentry_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this sentry change tracking
          configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/slack/:
    get:
      operationId: api_v1_environments_integrations_slack_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/SlackEnvironment'
          description: ''
    post:
      operationId: api_v1_environments_integrations_slack_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SlackEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SlackEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SlackEnvironment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/slack-channels/:
    get:
      operationId: api_v1_environments_integrations_slack_channels_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/SlackChannelList'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/slack/{id}/:
    get:
      operationId: api_v1_environments_integrations_slack_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this slack environment.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
    put:
      operationId: api_v1_environments_integrations_slack_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this slack environment.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SlackEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SlackEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SlackEnvironment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_slack_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this slack environment.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedSlackEnvironment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedSlackEnvironment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedSlackEnvironment'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_slack_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this slack environment.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/integrations/slack/callback/:
    get:
      operationId: api_v1_environments_integrations_slack_callback_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/slack/oauth/:
    get:
      operationId: api_v1_environments_integrations_slack_oauth_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/slack/signature/:
    get:
      operationId: api_v1_environments_integrations_slack_signature_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlackEnvironment'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/webhook/:
    get:
      operationId: api_v1_environments_integrations_webhook_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/WebhookConfiguration'
          description: ''
    post:
      operationId: api_v1_environments_integrations_webhook_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebhookConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/WebhookConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/WebhookConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WebhookConfiguration'
          description: ''
  /api/v1/environments/{environment_api_key}/integrations/webhook/{id}/:
    get:
      operationId: api_v1_environments_integrations_webhook_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WebhookConfiguration'
          description: ''
    put:
      operationId: api_v1_environments_integrations_webhook_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebhookConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/WebhookConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/WebhookConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WebhookConfiguration'
          description: ''
    patch:
      operationId: api_v1_environments_integrations_webhook_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook configuration.
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedWebhookConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedWebhookConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedWebhookConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WebhookConfiguration'
          description: ''
    delete:
      operationId: api_v1_environments_integrations_webhook_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook configuration.
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/metrics/:
    get:
      operationId: api_v1_environments_metrics_list
      description: Get metrics for this environment.
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedEnvironmentMetricsList'
          description: ''
  /api/v1/environments/{environment_api_key}/user-group-permissions/:
    get:
      operationId: api_v1_environments_user_group_permissions_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ListUserPermissionGroupEnvironmentPermission'
          description: ''
    post:
      operationId: api_v1_environments_user_group_permissions_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          description: ''
  /api/v1/environments/{environment_api_key}/user-group-permissions/{id}/:
    get:
      operationId: api_v1_environments_user_group_permissions_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          environment permission.
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          description: ''
    put:
      operationId: api_v1_environments_user_group_permissions_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          environment permission.
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          description: ''
    patch:
      operationId: api_v1_environments_user_group_permissions_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          environment permission.
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserPermissionGroupEnvironmentPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserPermissionGroupEnvironmentPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserPermissionGroupEnvironmentPermission'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupEnvironmentPermission'
          description: ''
    delete:
      operationId: api_v1_environments_user_group_permissions_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          environment permission.
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/user-permissions/:
    get:
      operationId: api_v1_environments_user_permissions_list
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ListUserEnvironmentPermission'
          description: ''
    post:
      operationId: api_v1_environments_user_permissions_create
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          description: ''
  /api/v1/environments/{environment_api_key}/user-permissions/{id}/:
    get:
      operationId: api_v1_environments_user_permissions_retrieve
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user environment permission.
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          description: ''
    put:
      operationId: api_v1_environments_user_permissions_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user environment permission.
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          description: ''
    patch:
      operationId: api_v1_environments_user_permissions_partial_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user environment permission.
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserEnvironmentPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserEnvironmentPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserEnvironmentPermission'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserEnvironmentPermission'
          description: ''
    delete:
      operationId: api_v1_environments_user_permissions_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user environment permission.
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/warehouse-connections/:
    get:
      operationId: api_v1_environments_warehouse_connections_list
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/WarehouseConnection'
          description: ''
    post:
      operationId: api_v1_environments_warehouse_connections_create
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WarehouseConnection'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/WarehouseConnection'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/WarehouseConnection'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WarehouseConnection'
          description: ''
  /api/v1/environments/{environment_api_key}/warehouse-connections/{connection_id}/:
    get:
      operationId: api_v1_environments_warehouse_connections_retrieve
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: connection_id
        schema:
          type: integer
        description: A unique integer value identifying this warehouse connection.
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WarehouseConnection'
          description: ''
    put:
      operationId: api_v1_environments_warehouse_connections_update
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: connection_id
        schema:
          type: integer
        description: A unique integer value identifying this warehouse connection.
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WarehouseConnection'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/WarehouseConnection'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/WarehouseConnection'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WarehouseConnection'
          description: ''
    patch:
      operationId: api_v1_environments_warehouse_connections_partial_update
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: connection_id
        schema:
          type: integer
        description: A unique integer value identifying this warehouse connection.
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedWarehouseConnection'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedWarehouseConnection'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedWarehouseConnection'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WarehouseConnection'
          description: ''
    delete:
      operationId: api_v1_environments_warehouse_connections_destroy
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: connection_id
        schema:
          type: integer
        description: A unique integer value identifying this warehouse connection.
        required: true
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_api_key}/webhooks/:
    get:
      operationId: api_v1_environments_webhooks_list
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Webhooks
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Webhook'
          description: ''
    post:
      operationId: api_v1_environments_webhooks_create
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Webhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Webhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Webhook'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Webhook'
          description: ''
  /api/v1/environments/{environment_api_key}/webhooks/{id}/:
    put:
      operationId: api_v1_environments_webhooks_update
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook.
        required: true
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Webhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Webhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Webhook'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Webhook'
          description: ''
    patch:
      operationId: api_v1_environments_webhooks_partial_update
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook.
        required: true
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedWebhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedWebhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedWebhook'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Webhook'
          description: ''
    delete:
      operationId: api_v1_environments_webhooks_destroy
      description: |-
        Abstract base class for generic types.

        On Python 3.12 and newer, generic classes implicitly inherit from
        Generic when they declare a parameter list after the class's name::

            class Mapping[KT, VT]:
                def __getitem__(self, key: KT) -> VT:
                    ...
                # Etc.

        On older versions of Python, however, generic classes have to
        explicitly inherit from Generic.

        After a class has been declared to be generic, it can then be used as
        follows::

            def lookup_name[KT, VT](mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
                try:
                    return mapping[key]
                except KeyError:
                    return default
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this webhook.
        required: true
      tags:
      - Webhooks
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_pk}/features/{feature_pk}/versions/:
    get:
      operationId: api_v1_environments_features_versions_list
      parameters:
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedEnvironmentFeatureVersionList'
          description: ''
      x-gram:
        name: get_environment_feature_versions
        description: 'Retrieves version information for a feature flag in a specific
          environment. Use this tool for environments with v2 feature versioning (use_v2_feature_versioning:
          true).'
    post:
      operationId: api_v1_environments_features_versions_create
      parameters:
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnvironmentFeatureVersionCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EnvironmentFeatureVersionCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EnvironmentFeatureVersionCreate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentFeatureVersionCreate'
          description: ''
      x-gram:
        name: create_environment_feature_version
        description: 'Creates a new version for a feature flag in a specific environment.
          Use this tool for environments with v2 feature versioning (use_v2_feature_versioning:
          true).'
  /api/v1/environments/{environment_pk}/features/{feature_pk}/versions/{environment_feature_version_pk}/featurestates/:
    get:
      operationId: api_v1_environments_features_versions_featurestates_list
      parameters:
      - in: path
        name: environment_feature_version_pk
        schema:
          type:
          - string
          - 'null'
          format: uuid
        required: true
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          description: ''
      x-gram:
        name: get_environment_feature_version_states
        description: 'Retrieves feature state information for a specific version in
          an environment. Use this tool for environments with v2 feature versioning
          (use_v2_feature_versioning: true).'
    post:
      operationId: api_v1_environments_features_versions_featurestates_create
      parameters:
      - in: path
        name: environment_feature_version_pk
        schema:
          type:
          - string
          - 'null'
          format: uuid
        required: true
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          description: ''
      x-gram:
        name: create_environment_feature_version_state
        description: 'Creates a new feature state for a specific version in an environment.
          Use this tool for environments with v2 feature versioning (use_v2_feature_versioning:
          true).'
  /api/v1/environments/{environment_pk}/features/{feature_pk}/versions/{environment_feature_version_pk}/featurestates/{id}/:
    put:
      operationId: api_v1_environments_features_versions_featurestates_update
      parameters:
      - in: path
        name: environment_feature_version_pk
        schema:
          type:
          - string
          - 'null'
          format: uuid
        required: true
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          description: ''
      x-gram:
        name: update_environment_feature_version_state
        description: 'Updates an existing feature state for a specific version in
          an environment. Use this tool for environments with v2 feature versioning
          (use_v2_feature_versioning: true).'
    patch:
      operationId: api_v1_environments_features_versions_featurestates_partial_update
      parameters:
      - in: path
        name: environment_feature_version_pk
        schema:
          type:
          - string
          - 'null'
          format: uuid
        required: true
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCustomEnvironmentFeatureVersionFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCustomEnvironmentFeatureVersionFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCustomEnvironmentFeatureVersionFeatureState'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          description: ''
    delete:
      operationId: api_v1_environments_features_versions_featurestates_destroy
      parameters:
      - in: path
        name: environment_feature_version_pk
        schema:
          type:
          - string
          - 'null'
          format: uuid
        required: true
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_pk}/features/{feature_pk}/versions/{id}/:
    delete:
      operationId: api_v1_environments_features_versions_destroy
      parameters:
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: string
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/{environment_pk}/features/{feature_pk}/versions/{id}/publish/:
    post:
      operationId: api_v1_environments_features_versions_publish_create
      parameters:
      - in: path
        name: environment_pk
        schema:
          type: integer
        required: true
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: string
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnvironmentFeatureVersionPublish'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EnvironmentFeatureVersionPublish'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EnvironmentFeatureVersionPublish'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentFeatureVersionPublish'
          description: ''
      x-gram:
        name: publish_environment_feature_version
        description: 'Publishes a feature version to make it live in the environment.
          Use this tool for environments with v2 feature versioning (use_v2_feature_versioning:
          true).'
  /api/v1/environments/environments/{environment_api_key}/edge-identities-featurestates:
    put:
      operationId: api_v1_environments_environments_edge_identities_featurestates_update
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EdgeIdentityWithIdentifierFeatureStateRequestBody'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/EdgeIdentityWithIdentifierFeatureStateRequestBody'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/EdgeIdentityWithIdentifierFeatureStateRequestBody'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EdgeIdentityFeatureState'
          description: ''
    delete:
      operationId: api_v1_environments_environments_edge_identities_featurestates_destroy
      parameters:
      - in: path
        name: environment_api_key
        schema:
          type: string
        required: true
      tags:
      - Identities
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/environments/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_environments_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          pattern: ^[0-9a-f-]+$
        required: true
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvironmentSerializerWithMetadata'
          description: ''
  /api/v1/environments/permissions/:
    get:
      operationId: api_v1_environments_permissions_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Environments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedPermissionModelList'
          description: ''
  /api/v1/feature-health/{path}:
    post:
      operationId: api_v1_feature_health_create
      parameters:
      - in: path
        name: path
        schema:
          type: string
          pattern: ^.{0,100}$
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          description: No response body
  /api/v1/features/create-feature-export/:
    post:
      operationId: api_v1_features_create_feature_export_create
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateFeatureExport'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateFeatureExport'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateFeatureExport'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureExport'
          description: ''
  /api/v1/features/download-feature-export/{feature_export_id}/:
    get:
      operationId: api_v1_features_download_feature_export_retrieve
      description: This endpoint is to download a feature export file from a specific
        environment
      parameters:
      - in: path
        name: feature_export_id
        schema:
          type: integer
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                additionalProperties: true
          description: ''
  /api/v1/features/download-flagsmith-on-flagsmith/:
    get:
      operationId: api_v1_features_download_flagsmith_on_flagsmith_retrieve
      description: This endpoint is to download a feature export to enable Flagsmith
        on Flagsmith
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                additionalProperties: true
          description: ''
  /api/v1/features/feature-import/{environment_id}:
    post:
      operationId: api_v1_features_feature_import_create
      parameters:
      - in: path
        name: environment_id
        schema:
          type: integer
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureImportUpload'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureImportUpload'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureImportUpload'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureImport'
          description: ''
  /api/v1/features/feature-segments/:
    get:
      operationId: api_v1_features_feature_segments_list
      parameters:
      - in: query
        name: environment
        schema:
          type: integer
        required: true
      - in: query
        name: feature
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureSegmentListList'
          description: ''
      x-gram:
        name: list_feature_segments
        description: Lists segment overrides for a feature in an environment.
    post:
      operationId: api_v1_features_feature_segments_create
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureSegmentCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureSegmentCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureSegmentCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureSegmentCreate'
          description: ''
  /api/v1/features/feature-segments/{id}/:
    get:
      operationId: api_v1_features_feature_segments_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature segment.
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureSegmentList'
          description: ''
    put:
      operationId: api_v1_features_feature_segments_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature segment.
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureSegmentCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureSegmentCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureSegmentCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureSegmentCreate'
          description: ''
    patch:
      operationId: api_v1_features_feature_segments_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature segment.
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedFeatureSegmentCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedFeatureSegmentCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedFeatureSegmentCreate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureSegmentCreate'
          description: ''
    delete:
      operationId: api_v1_features_feature_segments_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature segment.
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
      x-gram:
        name: delete_feature_segment
        description: 'Deletes a segment override. Use this tool for environments without
          v2 feature versioning (use_v2_feature_versioning: false).'
  /api/v1/features/feature-segments/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_features_feature_segments_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          pattern: ^[0-9a-f-]+$
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureSegmentList'
          description: ''
  /api/v1/features/feature-segments/update-priorities/:
    post:
      operationId: api_v1_features_feature_segments_update_priorities_create
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/FeatureSegmentChangePriorities'
          application/x-www-form-urlencoded:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/FeatureSegmentChangePriorities'
          multipart/form-data:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/FeatureSegmentChangePriorities'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureSegmentListList'
          description: ''
  /api/v1/features/featurestates/:
    get:
      operationId: api_v1_features_featurestates_list
      parameters:
      - in: query
        name: environment
        schema:
          type: integer
        description: ID of the environment.
        required: true
      - in: query
        name: feature
        schema:
          type: integer
      - in: query
        name: feature_segment
        schema:
          type: integer
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedWritableNestedFeatureStateList'
          description: ''
    post:
      operationId: api_v1_features_featurestates_create
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WritableNestedFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/WritableNestedFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/WritableNestedFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WritableNestedFeatureState'
          description: ''
  /api/v1/features/featurestates/{id}/:
    put:
      operationId: api_v1_features_featurestates_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WritableNestedFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/WritableNestedFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/WritableNestedFeatureState'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WritableNestedFeatureState'
          description: ''
      x-gram:
        name: update_feature_state
        description: 'Updates a feature state, including its enabled status and value.
          Use this tool to update a segment override''s value for environments without
          v2 feature versioning (use_v2_feature_versioning: false).'
    patch:
      operationId: api_v1_features_featurestates_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature state.
        required: true
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedWritableNestedFeatureState'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedWritableNestedFeatureState'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedWritableNestedFeatureState'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WritableNestedFeatureState'
          description: ''
  /api/v1/features/featurestates/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_features_featurestates_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          format: uuid
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WritableNestedFeatureState'
          description: ''
  /api/v1/features/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_features_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          format: uuid
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateFeature'
          description: ''
  /api/v1/flags/:
    get:
      operationId: sdk_v1_flags
      description: |-
        Retrieve the flags for an environment.

        ---
        *Note*: when providing the `feature` query argument, this endpoint will
        return either a single object or a 404 (if the feature does not exist) rather
        than a list.

        ---
        *Note*: using this endpoint with an identifier is deprecated.
        Please use `/api/v1/identities/?identifier=<identifier>` instead.
      parameters:
      - in: query
        name: feature
        schema:
          type: string
          minLength: 1
        description: Name of the feature to get the state of
      tags:
      - sdk
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  description: Represents a single flag (feature state) returned by
                    the Flagsmith SDK.
                  properties:
                    feature:
                      type: object
                      description: Represents a Flagsmith feature, defined at project
                        level.
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                        type:
                          enum:
                          - STANDARD
                          - MULTIVARIATE
                          type: string
                      required:
                      - id
                      - name
                      - type
                    enabled:
                      type: boolean
                    feature_state_value:
                      oneOf:
                      - type: integer
                      - type: boolean
                      - type: string
                      nullable: true
                  required:
                  - enabled
                  - feature
                  - feature_state_value
          description: ''
  /api/v1/flags/{feature_id}/multivariate-options/:
    get:
      operationId: api_v1_flags_multivariate_options_list
      parameters:
      - in: path
        name: feature_id
        schema:
          type: string
          pattern: ^[0-9]+$
        required: true
      tags:
      - Features
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/FeatureMVOptionsValuesResponse'
          description: ''
  /api/v1/flags/{identifier}:
    get:
      operationId: sdk_v1_flags_2
      description: |-
        Retrieve the flags for an environment.

        ---
        *Note*: when providing the `feature` query argument, this endpoint will
        return either a single object or a 404 (if the feature does not exist) rather
        than a list.

        ---
        *Note*: using this endpoint with an identifier is deprecated.
        Please use `/api/v1/identities/?identifier=<identifier>` instead.
      parameters:
      - in: query
        name: feature
        schema:
          type: string
          minLength: 1
        description: Name of the feature to get the state of
      - in: path
        name: identifier
        schema:
          type: string
          pattern: ^[-\w@%.]+$
        required: true
      tags:
      - sdk
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  description: Represents a single flag (feature state) returned by
                    the Flagsmith SDK.
                  properties:
                    feature:
                      type: object
                      description: Represents a Flagsmith feature, defined at project
                        level.
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                        type:
                          enum:
                          - STANDARD
                          - MULTIVARIATE
                          type: string
                      required:
                      - id
                      - name
                      - type
                    enabled:
                      type: boolean
                    feature_state_value:
                      oneOf:
                      - type: integer
                      - type: boolean
                      - type: string
                      nullable: true
                  required:
                  - enabled
                  - feature
                  - feature_state_value
          description: ''
  /api/v1/github-webhook/:
    post:
      operationId: api_v1_github_webhook_create
      tags:
      - Webhooks
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          description: No response body
  /api/v1/gitlab-webhook/{webhook_uuid}/:
    post:
      operationId: api_v1_gitlab_webhook_create
      parameters:
      - in: path
        name: webhook_uuid
        schema:
          type: string
          format: uuid
        required: true
      tags:
      - Other
      security:
      - tokenAuth: []
      - Master API Key: []
      - {}
      responses:
        '200':
          description: No response body
  /api/v1/identities/:
    get:
      operationId: sdk_v1_get_identities
      description: Retrieve the flags and traits for an identity.
      parameters:
      - in: query
        name: identifier
        schema:
          type: string
          minLength: 1
        required: true
      - in: query
        name: transient
        schema:
          type: boolean
          default: false
      tags:
      - sdk
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/V1IdentitiesResponse'
          description: ''
    post:
      operationId: sdk_v1_post_identities
      description: Identify a user, set their traits, and retrieve their flags.
      tags:
      - sdk
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/V1IdentitiesRequest'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/V1IdentitiesRequest'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/V1IdentitiesRequest'
        required: true
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/V1IdentitiesResponse'
          description: ''
  /api/v1/metadata/fields/:
    get:
      operationId: api_v1_metadata_fields_list
      parameters:
      - in: query
        name: organisation
        schema:
          type: integer
        description: Organisation ID to filter by
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      tags:
      - Metadata
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedMetadataFieldList'
          description: ''
    post:
      operationId: api_v1_metadata_fields_create
      tags:
      - Metadata
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MetadataField'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MetadataField'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MetadataField'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetadataField'
          description: ''
  /api/v1/metadata/fields/{id}/:
    get:
      operationId: api_v1_metadata_fields_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata field.
        required: true
      tags:
      - Metadata
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetadataField'
          description: ''
    put:
      operationId: api_v1_metadata_fields_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata field.
        required: true
      tags:
      - Metadata
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MetadataField'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MetadataField'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MetadataField'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetadataField'
          description: ''
    patch:
      operationId: api_v1_metadata_fields_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata field.
        required: true
      tags:
      - Metadata
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedMetadataField'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedMetadataField'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedMetadataField'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetadataField'
          description: ''
    delete:
      operationId: api_v1_metadata_fields_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata field.
        required: true
      tags:
      - Metadata
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/multivariate/options/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_multivariate_options_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          format: uuid
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MultivariateFeatureOption'
          description: ''
  /api/v1/oauth/authorize/:
    get:
      operationId: api_v1_oauth_authorize_retrieve
      description: Validate an authorisation request and return application info.
      tags:
      - Other
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
    post:
      operationId: api_v1_oauth_authorize_create
      description: Process a consent decision and return the redirect URI.
      tags:
      - Other
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/onboarding/request/send/:
    post:
      operationId: api_v1_onboarding_request_send_create
      tags:
      - Onboarding
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SelfHostedOnboardingSupportSendRequest'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SelfHostedOnboardingSupportSendRequest'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SelfHostedOnboardingSupportSendRequest'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
        '400':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: ''
  /api/v1/organisations/:
    get:
      operationId: api_v1_organisations_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedOrganisationSerializerFullList'
          description: ''
      x-gram:
        name: list_organizations
        description: Lists all organizations accessible with the provided user API
          key.
    post:
      operationId: api_v1_organisations_create
      description: Override create method to add new organisation to authenticated
        user
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrganisationSerializerFull'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/OrganisationSerializerFull'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/OrganisationSerializerFull'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
  /api/v1/organisations/{organisation_pk}/api-usage-notification/:
    get:
      operationId: api_v1_organisations_api_usage_notification_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedOrganisationAPIUsageNotificationList'
          description: ''
  /api/v1/organisations/{organisation_pk}/audit/:
    get:
      operationId: api_v1_organisations_audit_list
      parameters:
      - in: query
        name: environments
        schema:
          type: array
          items:
            type: integer
            minimum: 0
      - in: query
        name: is_system_event
        schema:
          type:
          - boolean
          - 'null'
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      - in: query
        name: project
        schema:
          type: integer
      - in: query
        name: search
        schema:
          type: string
          maxLength: 256
          minLength: 1
      tags:
      - Audit
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedAuditLogListList'
          description: ''
  /api/v1/organisations/{organisation_pk}/audit/{id}/:
    get:
      operationId: api_v1_organisations_audit_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this audit log.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Audit
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuditLogRetrieve'
          description: ''
  /api/v1/organisations/{organisation_pk}/github/create-cleanup-issue/:
    post:
      operationId: api_v1_organisations_github_create_cleanup_issue_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/github/issues/:
    get:
      operationId: api_v1_organisations_github_issues_retrieve
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/github/pulls/:
    get:
      operationId: api_v1_organisations_github_pulls_retrieve
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/github/repo-contributors/:
    get:
      operationId: api_v1_organisations_github_repo_contributors_retrieve
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/github/repositories/:
    get:
      operationId: api_v1_organisations_github_repositories_retrieve
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/groups/:
    get:
      operationId: api_v1_organisations_groups_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedListUserPermissionGroupList'
          description: ''
      x-gram:
        name: list_organization_groups
        description: Retrieves all permission groups within the organization.
    post:
      operationId: api_v1_organisations_groups_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListUserPermissionGroup'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/ListUserPermissionGroup'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/ListUserPermissionGroup'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListUserPermissionGroup'
          description: ''
  /api/v1/organisations/{organisation_pk}/groups/{group_pk}/users/{user_pk}/make-admin:
    post:
      operationId: api_v1_organisations_groups_users_make_admin_create
      parameters:
      - in: path
        name: group_pk
        schema:
          type: integer
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: path
        name: user_pk
        schema:
          type: integer
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/groups/{group_pk}/users/{user_pk}/remove-admin:
    post:
      operationId: api_v1_organisations_groups_users_remove_admin_create
      parameters:
      - in: path
        name: group_pk
        schema:
          type: integer
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: path
        name: user_pk
        schema:
          type: integer
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/organisations/{organisation_pk}/groups/{id}/:
    get:
      operationId: api_v1_organisations_groups_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupSerializerDetail'
          description: ''
    put:
      operationId: api_v1_organisations_groups_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListUserPermissionGroup'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/ListUserPermissionGroup'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/ListUserPermissionGroup'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListUserPermissionGroup'
          description: ''
    patch:
      operationId: api_v1_organisations_groups_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedListUserPermissionGroup'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedListUserPermissionGroup'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedListUserPermissionGroup'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListUserPermissionGroup'
          description: ''
    delete:
      operationId: api_v1_organisations_groups_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/groups/{id}/add-users/:
    post:
      operationId: api_v1_organisations_groups_add_users_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserIds'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserIds'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserIds'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupSerializerDetail'
          description: ''
  /api/v1/organisations/{organisation_pk}/groups/{id}/remove-users/:
    post:
      operationId: api_v1_organisations_groups_remove_users_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserIds'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserIds'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserIds'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupSerializerDetail'
          description: ''
  /api/v1/organisations/{organisation_pk}/groups/my-groups/:
    get:
      operationId: api_v1_organisations_groups_my_groups_retrieve
      description: Returns a list of summary group objects only for the groups a user
        is a member of.
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupSummary'
          description: ''
  /api/v1/organisations/{organisation_pk}/groups/summaries/:
    get:
      operationId: api_v1_organisations_groups_summaries_retrieve
      description: Returns a list of summary group objects for all groups in the organisation.
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupSummary'
          description: ''
  /api/v1/organisations/{organisation_pk}/integrations/github/:
    get:
      operationId: api_v1_organisations_integrations_github_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedGithubConfigurationList'
          description: ''
    post:
      operationId: api_v1_organisations_integrations_github_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GithubConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GithubConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GithubConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubConfiguration'
          description: ''
  /api/v1/organisations/{organisation_pk}/integrations/github/{github_pk}/repositories/:
    get:
      operationId: api_v1_organisations_integrations_github_repositories_list
      parameters:
      - in: path
        name: github_pk
        schema:
          type: string
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedGithubRepositoryList'
          description: ''
    post:
      operationId: api_v1_organisations_integrations_github_repositories_create
      parameters:
      - in: path
        name: github_pk
        schema:
          type: string
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GithubRepository'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GithubRepository'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GithubRepository'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubRepository'
          description: ''
  /api/v1/organisations/{organisation_pk}/integrations/github/{github_pk}/repositories/{id}/:
    get:
      operationId: api_v1_organisations_integrations_github_repositories_retrieve
      parameters:
      - in: path
        name: github_pk
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git hub repository.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubRepository'
          description: ''
    put:
      operationId: api_v1_organisations_integrations_github_repositories_update
      parameters:
      - in: path
        name: github_pk
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git hub repository.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GithubRepository'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GithubRepository'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GithubRepository'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubRepository'
          description: ''
    patch:
      operationId: api_v1_organisations_integrations_github_repositories_partial_update
      parameters:
      - in: path
        name: github_pk
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git hub repository.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedGithubRepository'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedGithubRepository'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedGithubRepository'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubRepository'
          description: ''
    delete:
      operationId: api_v1_organisations_integrations_github_repositories_destroy
      parameters:
      - in: path
        name: github_pk
        schema:
          type: string
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git hub repository.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/integrations/github/{id}/:
    get:
      operationId: api_v1_organisations_integrations_github_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this github configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubConfiguration'
          description: ''
    put:
      operationId: api_v1_organisations_integrations_github_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this github configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GithubConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GithubConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GithubConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubConfiguration'
          description: ''
    patch:
      operationId: api_v1_organisations_integrations_github_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this github configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedGithubConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedGithubConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedGithubConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GithubConfiguration'
          description: ''
    delete:
      operationId: api_v1_organisations_integrations_github_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this github configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/integrations/grafana/:
    get:
      operationId: api_v1_organisations_integrations_grafana_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          description: ''
    post:
      operationId: api_v1_organisations_integrations_grafana_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          description: ''
  /api/v1/organisations/{organisation_pk}/integrations/grafana/{id}/:
    get:
      operationId: api_v1_organisations_integrations_grafana_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana organisation
          configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          description: ''
    put:
      operationId: api_v1_organisations_integrations_grafana_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana organisation
          configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          description: ''
    patch:
      operationId: api_v1_organisations_integrations_grafana_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana organisation
          configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaOrganisationConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaOrganisationConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaOrganisationConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaOrganisationConfiguration'
          description: ''
    delete:
      operationId: api_v1_organisations_integrations_grafana_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana organisation
          configuration.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/invite-links/:
    get:
      operationId: api_v1_organisations_invite_links_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/InviteLink'
          description: ''
    post:
      operationId: api_v1_organisations_invite_links_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InviteLink'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/InviteLink'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/InviteLink'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InviteLink'
          description: ''
  /api/v1/organisations/{organisation_pk}/invite-links/{id}/:
    delete:
      operationId: api_v1_organisations_invite_links_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this invite link.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/invites/:
    get:
      operationId: api_v1_organisations_invites_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedInviteListList'
          description: ''
      x-gram:
        name: list_organization_invites
        description: Retrieves all pending invitations for the organization.
    post:
      operationId: api_v1_organisations_invites_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Invite'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Invite'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Invite'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Invite'
          description: ''
      x-gram:
        name: create_organization_invite
        description: Send an invitation to join the organization with specified role
          and permissions.
  /api/v1/organisations/{organisation_pk}/invites/{id}/:
    get:
      operationId: api_v1_organisations_invites_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this invite.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InviteList'
          description: ''
    delete:
      operationId: api_v1_organisations_invites_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this invite.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/invites/{id}/resend/:
    post:
      operationId: api_v1_organisations_invites_resend_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this invite.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InviteList'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/InviteList'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/InviteList'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InviteList'
          description: ''
  /api/v1/organisations/{organisation_pk}/master-api-keys/:
    get:
      operationId: api_v1_organisations_master_api_keys_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Organisations
      security:
      - tokenAuth: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedMasterAPIKeyList'
          description: ''
    post:
      operationId: api_v1_organisations_master_api_keys_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MasterAPIKey'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MasterAPIKey'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MasterAPIKey'
      security:
      - tokenAuth: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MasterAPIKey'
          description: ''
  /api/v1/organisations/{organisation_pk}/master-api-keys/{prefix}/:
    get:
      operationId: api_v1_organisations_master_api_keys_retrieve
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: path
        name: prefix
        schema:
          type: string
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MasterAPIKey'
          description: ''
    put:
      operationId: api_v1_organisations_master_api_keys_update
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: path
        name: prefix
        schema:
          type: string
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MasterAPIKey'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MasterAPIKey'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MasterAPIKey'
      security:
      - tokenAuth: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MasterAPIKey'
          description: ''
    patch:
      operationId: api_v1_organisations_master_api_keys_partial_update
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: path
        name: prefix
        schema:
          type: string
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedMasterAPIKey'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedMasterAPIKey'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedMasterAPIKey'
      security:
      - tokenAuth: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MasterAPIKey'
          description: ''
    delete:
      operationId: api_v1_organisations_master_api_keys_destroy
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: path
        name: prefix
        schema:
          type: string
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/metadata-model-fields/:
    get:
      operationId: api_v1_organisations_metadata_model_fields_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedMetaDataModelFieldList'
          description: ''
    post:
      operationId: api_v1_organisations_metadata_model_fields_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MetaDataModelField'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MetaDataModelField'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MetaDataModelField'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetaDataModelField'
          description: ''
  /api/v1/organisations/{organisation_pk}/metadata-model-fields/{id}/:
    get:
      operationId: api_v1_organisations_metadata_model_fields_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata model field.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetaDataModelField'
          description: ''
    put:
      operationId: api_v1_organisations_metadata_model_fields_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata model field.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MetaDataModelField'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MetaDataModelField'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MetaDataModelField'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetaDataModelField'
          description: ''
    patch:
      operationId: api_v1_organisations_metadata_model_fields_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata model field.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedMetaDataModelField'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedMetaDataModelField'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedMetaDataModelField'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetaDataModelField'
          description: ''
    delete:
      operationId: api_v1_organisations_metadata_model_fields_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata model field.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/metadata-model-fields/supported-content-types/:
    get:
      operationId: api_v1_organisations_metadata_model_fields_supported_content_types_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedContentTypeList'
          description: ''
  /api/v1/organisations/{organisation_pk}/metadata-model-fields/supported-required-for-models/:
    get:
      operationId: api_v1_organisations_metadata_model_fields_supported_required_for_models_list
      parameters:
      - in: query
        name: model_name
        schema:
          type: string
          minLength: 1
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedContentTypeList'
          description: ''
  /api/v1/organisations/{organisation_pk}/usage-data/:
    get:
      operationId: api_v1_organisations_usage_data_retrieve
      parameters:
      - in: query
        name: client_application_name
        schema:
          type:
          - string
          - 'null'
      - in: query
        name: client_application_version
        schema:
          type:
          - string
          - 'null'
      - in: query
        name: environment_id
        schema:
          type: integer
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: query
        name: period
        schema:
          enum:
          - current_billing_period
          - previous_billing_period
          - 90_day_period
          - null
          type:
          - string
          - 'null'
        description: |-
          * `current_billing_period` - current_billing_period
          * `previous_billing_period` - previous_billing_period
          * `90_day_period` - 90_day_period
      - in: query
        name: project_id
        schema:
          type: integer
      - in: query
        name: user_agent
        schema:
          type:
          - string
          - 'null'
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UsageData'
          description: ''
  /api/v1/organisations/{organisation_pk}/usage-data/total-count/:
    get:
      operationId: api_v1_organisations_usage_data_total_count_retrieve
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UsageTotalCount'
          description: ''
  /api/v1/organisations/{organisation_pk}/user-group-permissions/:
    get:
      operationId: api_v1_organisations_user_group_permissions_list
      parameters:
      - in: query
        name: group
        schema:
          type: integer
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionList'
          description: ''
    post:
      operationId: api_v1_organisations_user_group_permissions_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          description: ''
  /api/v1/organisations/{organisation_pk}/user-group-permissions/{id}/:
    put:
      operationId: api_v1_organisations_user_group_permissions_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          organisation permission.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          description: ''
    patch:
      operationId: api_v1_organisations_user_group_permissions_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          organisation permission.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedUserPermissionGroupOrganisationPermissionUpdateCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedUserPermissionGroupOrganisationPermissionUpdateCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedUserPermissionGroupOrganisationPermissionUpdateCreate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissionGroupOrganisationPermissionUpdateCreate'
          description: ''
    delete:
      operationId: api_v1_organisations_user_group_permissions_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user permission group
          organisation permission.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/user-permissions/:
    get:
      operationId: api_v1_organisations_user_permissions_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - in: query
        name: user
        schema:
          type: integer
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/UserOrganisationPermissionList'
          description: ''
    post:
      operationId: api_v1_organisations_user_permissions_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          description: ''
  /api/v1/organisations/{organisation_pk}/user-permissions/{id}/:
    put:
      operationId: api_v1_organisations_user_permissions_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user organisation permission.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          description: ''
    patch:
      operationId: api_v1_organisations_user_permissions_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user organisation permission.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedUserOrganisationPermissionUpdateCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedUserOrganisationPermissionUpdateCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedUserOrganisationPermissionUpdateCreate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserOrganisationPermissionUpdateCreate'
          description: ''
    delete:
      operationId: api_v1_organisations_user_permissions_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user organisation permission.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{organisation_pk}/users/:
    get:
      operationId: api_v1_organisations_users_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/UserList'
          description: ''
  /api/v1/organisations/{organisation_pk}/users/{id}/update-role/:
    post:
      operationId: api_v1_organisations_users_update_role_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this Feature flag admin user.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: string
        required: true
      tags:
      - Authentication
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserOrganisation'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserOrganisation'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserOrganisation'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserOrganisation'
          description: ''
  /api/v1/organisations/{organisation_pk}/webhooks/:
    get:
      operationId: api_v1_organisations_webhooks_list
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - Webhooks
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedOrganisationWebhookList'
          description: ''
    post:
      operationId: api_v1_organisations_webhooks_create
      parameters:
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrganisationWebhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/OrganisationWebhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/OrganisationWebhook'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationWebhook'
          description: ''
  /api/v1/organisations/{organisation_pk}/webhooks/{id}/:
    get:
      operationId: api_v1_organisations_webhooks_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation webhook.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Webhooks
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationWebhook'
          description: ''
    put:
      operationId: api_v1_organisations_webhooks_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation webhook.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrganisationWebhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/OrganisationWebhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/OrganisationWebhook'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationWebhook'
          description: ''
    patch:
      operationId: api_v1_organisations_webhooks_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation webhook.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedOrganisationWebhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedOrganisationWebhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedOrganisationWebhook'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationWebhook'
          description: ''
    delete:
      operationId: api_v1_organisations_webhooks_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation webhook.
        required: true
      - in: path
        name: organisation_pk
        schema:
          type: integer
        required: true
      tags:
      - Webhooks
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{id}/:
    get:
      operationId: api_v1_organisations_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
    put:
      operationId: api_v1_organisations_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrganisationSerializerFull'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/OrganisationSerializerFull'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/OrganisationSerializerFull'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
    patch:
      operationId: api_v1_organisations_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedOrganisationSerializerFull'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedOrganisationSerializerFull'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedOrganisationSerializerFull'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
    delete:
      operationId: api_v1_organisations_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/organisations/{id}/get-hosted-page-url-for-subscription-upgrade/:
    post:
      operationId: api_v1_organisations_get_hosted_page_url_for_subscription_upgrade_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GetHostedPageForSubscriptionUpgrade'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GetHostedPageForSubscriptionUpgrade'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GetHostedPageForSubscriptionUpgrade'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetHostedPageForSubscriptionUpgrade'
          description: ''
  /api/v1/organisations/{id}/get-subscription-metadata/:
    get:
      operationId: api_v1_organisations_get_subscription_metadata_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SubscriptionDetails'
          description: ''
  /api/v1/organisations/{id}/influx-data/:
    get:
      operationId: api_v1_organisations_influx_data_retrieve
      description: Please use /api/v1/organisations/{organisation_pk}/usage-data/
      parameters:
      - in: query
        name: environment_id
        schema:
          type: integer
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      - in: query
        name: project_id
        schema:
          type: integer
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      deprecated: true
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InfluxData'
          description: ''
  /api/v1/organisations/{id}/invite/:
    post:
      operationId: api_v1_organisations_invite_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MultiInvites'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MultiInvites'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MultiInvites'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MultiInvites'
          description: ''
  /api/v1/organisations/{id}/my-permissions/:
    get:
      operationId: api_v1_organisations_my_permissions_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserObjectPermissions'
          description: ''
  /api/v1/organisations/{id}/portal-url/:
    get:
      operationId: api_v1_organisations_portal_url_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PortalUrl'
          description: ''
  /api/v1/organisations/{id}/projects/:
    get:
      operationId: api_v1_organisations_projects_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
      x-gram:
        name: list_projects_in_organization
        description: Retrieves all projects within a specified organization.
  /api/v1/organisations/{id}/remove-users/:
    post:
      operationId: api_v1_organisations_remove_users_create
      description: Takes a list of users and removes them from the organisation provided
        in the url
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserId'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UserId'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UserId'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserId'
          description: ''
  /api/v1/organisations/{id}/update-subscription/:
    post:
      operationId: api_v1_organisations_update_subscription_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateSubscription'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UpdateSubscription'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UpdateSubscription'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
  /api/v1/organisations/{id}/usage/:
    get:
      operationId: api_v1_organisations_usage_retrieve
      description: Please use /api/v1/organisations/{organisation_pk}/usage-data/total-count/
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      deprecated: true
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
  /api/v1/organisations/{id}/user-detailed-permissions/{user_id}/:
    get:
      operationId: api_v1_organisations_user_detailed_permissions_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this organisation.
        required: true
      - in: path
        name: user_id
        schema:
          type: string
          pattern: ^\d+$
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserDetailedPermissions'
          description: ''
  /api/v1/organisations/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_organisations_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          pattern: ^[0-9a-f-]+$
        required: true
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrganisationSerializerFull'
          description: ''
  /api/v1/organisations/permissions/:
    get:
      operationId: api_v1_organisations_permissions_retrieve
      tags:
      - Organisations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PermissionModel'
          description: ''
  /api/v1/projects/:
    get:
      operationId: api_v1_projects_list
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ProjectList'
          description: ''
    post:
      operationId: api_v1_projects_create
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectCreate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/ProjectCreate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/ProjectCreate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectCreate'
          description: ''
  /api/v1/projects/{id}/:
    get:
      operationId: api_v1_projects_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectRetrieve'
          description: ''
      x-gram:
        name: get_project
        description: Retrieves comprehensive information about a specific project
          including configuration and statistics.
    put:
      operationId: api_v1_projects_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectUpdate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/ProjectUpdate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/ProjectUpdate'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectUpdate'
          description: ''
      x-gram:
        name: update_project
        description: Updates project configuration settings such as the project name
          and feature visibility.
    patch:
      operationId: api_v1_projects_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedProjectUpdate'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedProjectUpdate'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedProjectUpdate'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectUpdate'
          description: ''
    delete:
      operationId: api_v1_projects_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{id}/environments/:
    get:
      operationId: api_v1_projects_environments_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectList'
          description: ''
      x-gram:
        name: list_project_environments
        description: Retrieves all environments configured for the specified project.
  /api/v1/projects/{id}/migrate-to-edge/:
    post:
      operationId: api_v1_projects_migrate_to_edge_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '202':
          description: No response body
  /api/v1/projects/{id}/my-permissions/:
    get:
      operationId: api_v1_projects_my_permissions_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserObjectPermissions'
          description: ''
  /api/v1/projects/{id}/user-detailed-permissions/{user_id}/:
    get:
      operationId: api_v1_projects_user_detailed_permissions_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this project.
        required: true
      - in: path
        name: user_id
        schema:
          type: string
          pattern: ^\d+$
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserDetailedPermissions'
          description: ''
  /api/v1/projects/{project_pk}/all-user-permissions/{user_pk}/:
    get:
      operationId: api_v1_projects_all_user_permissions_retrieve
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      - in: path
        name: user_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserObjectPermissions'
          description: ''
  /api/v1/projects/{project_pk}/audit/:
    get:
      operationId: api_v1_projects_audit_list
      parameters:
      - in: query
        name: environments
        schema:
          type: array
          items:
            type: integer
            minimum: 0
      - in: query
        name: is_system_event
        schema:
          type:
          - boolean
          - 'null'
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      - in: query
        name: project
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      - in: query
        name: search
        schema:
          type: string
          maxLength: 256
          minLength: 1
      tags:
      - Audit
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedAuditLogListList'
          description: ''
  /api/v1/projects/{project_pk}/audit/{id}/:
    get:
      operationId: api_v1_projects_audit_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this audit log.
        required: true
      - in: path
        name: project_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Audit
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuditLogRetrieve'
          description: ''
  /api/v1/projects/{project_pk}/code-references/:
    post:
      operationId: api_v1_projects_code_references_create
      description: API view to create code references for a project
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureFlagCodeReferencesScan'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureFlagCodeReferencesScan'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureFlagCodeReferencesScan'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureFlagCodeReferencesScan'
          description: ''
  /api/v1/projects/{project_pk}/feature-exports/:
    get:
      operationId: api_v1_projects_feature_exports_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureExportList'
          description: ''
  /api/v1/projects/{project_pk}/feature-health/events/:
    get:
      operationId: api_v1_projects_feature_health_events_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/FeatureHealthEvent'
          description: ''
      x-gram:
        name: get_feature_health_events
        description: Retrieves feature health monitoring events and metrics for the
          project.
  /api/v1/projects/{project_pk}/feature-health/events/{id}/dismiss/:
    post:
      operationId: api_v1_projects_feature_health_events_dismiss_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature health event.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureHealthEvent'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureHealthEvent'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureHealthEvent'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureHealthEvent'
          description: ''
  /api/v1/projects/{project_pk}/feature-health/providers/:
    get:
      operationId: api_v1_projects_feature_health_providers_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/FeatureHealthProvider'
          description: ''
    post:
      operationId: api_v1_projects_feature_health_providers_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Feature states
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateFeatureHealthProvider'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateFeatureHealthProvider'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateFeatureHealthProvider'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureHealthProvider'
          description: ''
  /api/v1/projects/{project_pk}/feature-health/providers/{name}/:
    delete:
      operationId: api_v1_projects_feature_health_providers_destroy
      parameters:
      - in: path
        name: name
        schema:
          enum:
          - Webhook
          - Grafana
          type: string
          description: |-
            * `Webhook` - Webhook
            * `Grafana` - Grafana
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Feature states
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/feature-imports/:
    get:
      operationId: api_v1_projects_feature_imports_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureImportList'
          description: ''
  /api/v1/projects/{project_pk}/features/:
    get:
      operationId: api_v1_projects_features_list
      parameters:
      - in: query
        name: environment
        schema:
          type: integer
        description: Integer ID of the environment to view features in the context
          of.
      - in: query
        name: group_owners
        schema:
          type: string
          minLength: 1
        description: Comma separated list of group owner ids to filter on
      - in: query
        name: identity
        schema:
          type: string
          minLength: 1
        description: ID of the identity to sort features with identity overrides first.
      - in: query
        name: is_archived
        schema:
          type: boolean
      - in: query
        name: is_enabled
        schema:
          type:
          - boolean
          - 'null'
        description: Boolean value to filter features as enabled or disabled.
      - in: query
        name: owners
        schema:
          type: string
          minLength: 1
        description: Comma separated list of owner ids to filter on
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      - in: query
        name: search
        schema:
          type: string
          minLength: 1
      - in: query
        name: segment
        schema:
          type: integer
        description: Integer ID of the segment to retrieve segment overrides for.
      - in: query
        name: sort_direction
        schema:
          enum:
          - ASC
          - DESC
          type: string
          default: ASC
          minLength: 1
        description: |-
          * `ASC` - ASC
          * `DESC` - DESC
      - in: query
        name: sort_field
        schema:
          enum:
          - created_date
          - name
          type: string
          default: created_date
          minLength: 1
        description: |-
          * `created_date` - created_date
          * `name` - name
      - in: query
        name: tag_strategy
        schema:
          enum:
          - UNION
          - INTERSECTION
          type: string
          default: INTERSECTION
          minLength: 1
        description: |-
          * `UNION` - UNION
          * `INTERSECTION` - INTERSECTION
      - in: query
        name: tags
        schema:
          type: string
          minLength: 1
        description: Comma separated list of tag ids to filter on (AND with INTERSECTION,
          and OR with UNION via tag_strategy)
      - in: query
        name: value_search
        schema:
          type: string
          minLength: 1
        description: Value of type int, string, or boolean to filter features based
          on their values
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedListFeatureList'
          description: ''
      x-gram:
        name: list_project_features
        description: Lists a project's feature flags (paginated). Pass `environment=<id>`
          to also get each feature's live state for that environment in `environment_feature_state`,
          along with override counts. Works for both v1 and v2 versioned environments.
    post:
      operationId: api_v1_projects_features_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListFeature'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/ListFeature'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/ListFeature'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListFeature'
          description: ''
      x-gram:
        name: create_feature
        description: Creates a new feature flag in the specified project with default
          settings.
  /api/v1/projects/{project_pk}/features/{feature_pk}/code-references/:
    get:
      operationId: api_v1_projects_features_code_references_retrieve
      description: API view to retrieve code references for a specific feature in
        a project
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureFlagCodeReferencesRepositorySummary'
          description: ''
      x-gram:
        name: get_feature_code_references
        description: Retrieves code references and usage information for the feature
          flag.
  /api/v1/projects/{project_pk}/features/{feature_pk}/feature-external-resources/:
    get:
      operationId: api_v1_projects_features_feature_external_resources_list
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedFeatureExternalResourceList'
          description: ''
      x-gram:
        name: get_feature_external_resources
        description: Retrieves external resources linked to the feature flag.
    post:
      operationId: api_v1_projects_features_feature_external_resources_create
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureExternalResource'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureExternalResource'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureExternalResource'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureExternalResource'
          description: ''
  /api/v1/projects/{project_pk}/features/{feature_pk}/feature-external-resources/{id}/:
    get:
      operationId: api_v1_projects_features_feature_external_resources_retrieve
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature external resource.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureExternalResource'
          description: ''
    put:
      operationId: api_v1_projects_features_feature_external_resources_update
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature external resource.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureExternalResource'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureExternalResource'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureExternalResource'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureExternalResource'
          description: ''
    patch:
      operationId: api_v1_projects_features_feature_external_resources_partial_update
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature external resource.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedFeatureExternalResource'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedFeatureExternalResource'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedFeatureExternalResource'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureExternalResource'
          description: ''
    delete:
      operationId: api_v1_projects_features_feature_external_resources_destroy
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature external resource.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/features/{feature_pk}/mv-options/:
    get:
      operationId: api_v1_projects_features_mv_options_list
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedMultivariateFeatureOptionList'
          description: ''
      x-gram:
        name: list_feature_multivariate_options
        description: Retrieves all multivariate options for a feature flag.
    post:
      operationId: api_v1_projects_features_mv_options_create
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MultivariateFeatureOption'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MultivariateFeatureOption'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MultivariateFeatureOption'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MultivariateFeatureOption'
          description: ''
      x-gram:
        name: create_feature_multivariate_option
        description: Creates a new multivariate option for a feature flag.
  /api/v1/projects/{project_pk}/features/{feature_pk}/mv-options/{id}/:
    get:
      operationId: api_v1_projects_features_mv_options_retrieve
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this multivariate feature
          option.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MultivariateFeatureOption'
          description: ''
    put:
      operationId: api_v1_projects_features_mv_options_update
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this multivariate feature
          option.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MultivariateFeatureOption'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/MultivariateFeatureOption'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/MultivariateFeatureOption'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MultivariateFeatureOption'
          description: ''
      x-gram:
        name: update_feature_multivariate_option
        description: Updates an existing multivariate option.
    patch:
      operationId: api_v1_projects_features_mv_options_partial_update
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this multivariate feature
          option.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedMultivariateFeatureOption'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedMultivariateFeatureOption'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedMultivariateFeatureOption'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MultivariateFeatureOption'
          description: ''
    delete:
      operationId: api_v1_projects_features_mv_options_destroy
      parameters:
      - in: path
        name: feature_pk
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this multivariate feature
          option.
        required: true
      - in: path
        name: project_pk
        schema:
          type: string
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
      x-gram:
        name: delete_feature_multivariate_option
        description: Deletes a multivariate option.
  /api/v1/projects/{project_pk}/features/{id}/:
    get:
      operationId: api_v1_projects_features_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListFeature'
          description: ''
      x-gram:
        name: get_feature_flag
        description: Retrieves detailed information about a specific feature flag.
    put:
      operationId: api_v1_projects_features_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateFeature'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/UpdateFeature'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/UpdateFeature'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateFeature'
          description: ''
      x-gram:
        name: update_feature
        description: Updates feature flag properties such as name and description.
    patch:
      operationId: api_v1_projects_features_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedUpdateFeature'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedUpdateFeature'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedUpdateFeature'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateFeature'
          description: ''
    delete:
      operationId: api_v1_projects_features_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/features/{id}/add-group-owners/:
    post:
      operationId: api_v1_projects_features_add_group_owners_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureGroupOwnerInput'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureGroupOwnerInput'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureGroupOwnerInput'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectFeature'
          description: ''
  /api/v1/projects/{project_pk}/features/{id}/add-owners/:
    post:
      operationId: api_v1_projects_features_add_owners_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureOwnerInput'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureOwnerInput'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureOwnerInput'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectFeature'
          description: ''
  /api/v1/projects/{project_pk}/features/{id}/evaluation-data/:
    get:
      operationId: api_v1_projects_features_evaluation_data_retrieve
      parameters:
      - in: query
        name: client_application_name
        schema:
          type:
          - string
          - 'null'
      - in: query
        name: client_application_version
        schema:
          type:
          - string
          - 'null'
      - in: query
        name: environment_id
        schema:
          type: integer
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: query
        name: period
        schema:
          type: integer
          default: 30
        description: number of days
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      - in: query
        name: user_agent
        schema:
          type:
          - string
          - 'null'
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureEvaluationData'
          description: ''
      x-gram:
        name: get_feature_evaluation_data
        description: Retrieves evaluation data and analytics for a specific feature
          flag.
  /api/v1/projects/{project_pk}/features/{id}/influx-data/:
    get:
      operationId: api_v1_projects_features_influx_data_retrieve
      description: Please use ​/api​/v1​/projects​/{project_pk}​/features​/{id}​/evaluation-data/
      parameters:
      - in: query
        name: aggregate_every
        schema:
          type: string
          default: 24h
          minLength: 1
      - in: query
        name: environment_id
        schema:
          type: string
          minLength: 1
        required: true
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: query
        name: period
        schema:
          type: string
          default: 24h
          minLength: 1
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      security:
      - tokenAuth: []
      - Master API Key: []
      deprecated: true
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FeatureInfluxData'
          description: ''
  /api/v1/projects/{project_pk}/features/{id}/remove-group-owners/:
    post:
      operationId: api_v1_projects_features_remove_group_owners_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureGroupOwnerInput'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureGroupOwnerInput'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureGroupOwnerInput'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectFeature'
          description: ''
  /api/v1/projects/{project_pk}/features/{id}/remove-owners/:
    post:
      operationId: api_v1_projects_features_remove_owners_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this feature.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        required: true
      tags:
      - Features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeatureOwnerInput'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/FeatureOwnerInput'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/FeatureOwnerInput'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectFeature'
          description: ''
  /api/v1/projects/{project_pk}/gitlab/issues/:
    get:
      operationId: api_v1_projects_gitlab_issues_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedSearchQueryParamsList'
          description: ''
  /api/v1/projects/{project_pk}/gitlab/merge-requests/:
    get:
      operationId: api_v1_projects_gitlab_merge_requests_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedSearchQueryParamsList'
          description: ''
  /api/v1/projects/{project_pk}/gitlab/projects/:
    get:
      operationId: api_v1_projects_gitlab_projects_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedPaginatedQueryParamsList'
          description: ''
  /api/v1/projects/{project_pk}/imports/launch-darkly/:
    get:
      operationId: api_v1_projects_imports_launch_darkly_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LaunchDarklyImportRequest'
          description: ''
    post:
      operationId: api_v1_projects_imports_launch_darkly_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateLaunchDarklyImportRequest'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateLaunchDarklyImportRequest'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateLaunchDarklyImportRequest'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LaunchDarklyImportRequest'
          description: ''
  /api/v1/projects/{project_pk}/imports/launch-darkly/{id}/:
    get:
      operationId: api_v1_projects_imports_launch_darkly_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this launch darkly import
          request.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LaunchDarklyImportRequest'
          description: ''
  /api/v1/projects/{project_pk}/integrations/datadog/:
    get:
      operationId: api_v1_projects_integrations_datadog_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/DataDogConfiguration'
          description: ''
    post:
      operationId: api_v1_projects_integrations_datadog_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DataDogConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/DataDogConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/DataDogConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DataDogConfiguration'
          description: ''
  /api/v1/projects/{project_pk}/integrations/datadog/{id}/:
    get:
      operationId: api_v1_projects_integrations_datadog_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this data dog configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DataDogConfiguration'
          description: ''
    put:
      operationId: api_v1_projects_integrations_datadog_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this data dog configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DataDogConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/DataDogConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/DataDogConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DataDogConfiguration'
          description: ''
    patch:
      operationId: api_v1_projects_integrations_datadog_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this data dog configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedDataDogConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedDataDogConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedDataDogConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DataDogConfiguration'
          description: ''
    delete:
      operationId: api_v1_projects_integrations_datadog_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this data dog configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/integrations/gitlab/:
    get:
      operationId: api_v1_projects_integrations_gitlab_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GitLabConfiguration'
          description: ''
    post:
      operationId: api_v1_projects_integrations_gitlab_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GitLabConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GitLabConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GitLabConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GitLabConfiguration'
          description: ''
  /api/v1/projects/{project_pk}/integrations/gitlab/{id}/:
    get:
      operationId: api_v1_projects_integrations_gitlab_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git lab configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GitLabConfiguration'
          description: ''
    put:
      operationId: api_v1_projects_integrations_gitlab_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git lab configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GitLabConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GitLabConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GitLabConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GitLabConfiguration'
          description: ''
    patch:
      operationId: api_v1_projects_integrations_gitlab_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git lab configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedGitLabConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedGitLabConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedGitLabConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GitLabConfiguration'
          description: ''
    delete:
      operationId: api_v1_projects_integrations_gitlab_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this git lab configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/integrations/grafana/:
    get:
      operationId: api_v1_projects_integrations_grafana_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    post:
      operationId: api_v1_projects_integrations_grafana_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
  /api/v1/projects/{project_pk}/integrations/grafana/{id}/:
    get:
      operationId: api_v1_projects_integrations_grafana_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    put:
      operationId: api_v1_projects_integrations_grafana_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GrafanaProjectConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    patch:
      operationId: api_v1_projects_integrations_grafana_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaProjectConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaProjectConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedGrafanaProjectConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GrafanaProjectConfiguration'
          description: ''
    delete:
      operationId: api_v1_projects_integrations_grafana_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this grafana project configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/integrations/new-relic/:
    get:
      operationId: api_v1_projects_integrations_new_relic_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/NewRelicConfiguration'
          description: ''
    post:
      operationId: api_v1_projects_integrations_new_relic_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewRelicConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/NewRelicConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/NewRelicConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NewRelicConfiguration'
          description: ''
  /api/v1/projects/{project_pk}/integrations/new-relic/{id}/:
    get:
      operationId: api_v1_projects_integrations_new_relic_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this new relic configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NewRelicConfiguration'
          description: ''
    put:
      operationId: api_v1_projects_integrations_new_relic_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this new relic configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewRelicConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/NewRelicConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/NewRelicConfiguration'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NewRelicConfiguration'
          description: ''
    patch:
      operationId: api_v1_projects_integrations_new_relic_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this new relic configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedNewRelicConfiguration'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedNewRelicConfiguration'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedNewRelicConfiguration'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NewRelicConfiguration'
          description: ''
    delete:
      operationId: api_v1_projects_integrations_new_relic_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this new relic configuration.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Integrations
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/metadata/fields/:
    get:
      operationId: api_v1_projects_metadata_fields_list
      parameters:
      - in: query
        name: entity
        schema:
          enum:
          - feature
          - segment
          - environment
          type: string
          minLength: 1
        description: |-
          Filter by entity type (feature, segment, or environment).

          * `feature` - feature
          * `segment` - segment
          * `environment` - environment
      - in: query
        name: include_organisation
        schema:
          type: boolean
          default: false
        description: Include inherited organisation-level fields. Project-level fields
          override same-named org fields.
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Metadata
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedMetadataFieldList'
          description: ''
  /api/v1/projects/{project_pk}/metadata/fields/{id}/:
    get:
      operationId: api_v1_projects_metadata_fields_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this metadata field.
        required: true
      - in: path
        name: project_pk
        schema:
          type:
          - integer
          - 'null'
        required: true
      tags:
      - Metadata
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetadataField'
          description: ''
  /api/v1/projects/{project_pk}/segments/:
    get:
      operationId: api_v1_projects_segments_list
      parameters:
      - in: query
        name: identity
        schema:
          type: string
          minLength: 1
        description: Optionally provide the id of an identity to get only the segments
          they match
      - in: query
        name: include_feature_specific
        schema:
          type: boolean
          default: true
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - name: page_size
        required: false
        in: query
        description: Number of results to return per page.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      - in: query
        name: q
        schema:
          type: string
          minLength: 1
        description: Search term to find segment with given term in their name
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedSegmentList'
          description: ''
      x-gram:
        name: list_project_segments
        description: Retrieves all user segments defined for audience targeting within
          the project.
    post:
      operationId: api_v1_projects_segments_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Segment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Segment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Segment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Segment'
          description: ''
      x-gram:
        name: create_project_segment
        description: Creates a new user segment for audience targeting within the
          project.
  /api/v1/projects/{project_pk}/segments/{id}/:
    get:
      operationId: api_v1_projects_segments_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Segment'
          description: ''
      x-gram:
        name: get_project_segment
        description: Retrieves detailed information about a specific user segment.
    put:
      operationId: api_v1_projects_segments_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - mcp
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Segment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Segment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Segment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Segment'
          description: ''
      x-gram:
        name: update_project_segment
        description: Updates an existing user segment's properties and rules.
    patch:
      operationId: api_v1_projects_segments_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Segments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedSegment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedSegment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedSegment'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Segment'
          description: ''
    delete:
      operationId: api_v1_projects_segments_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Segments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/segments/{id}/associated-features/:
    get:
      operationId: api_v1_projects_segments_associated_features_retrieve
      parameters:
      - in: query
        name: environment
        schema:
          type: integer
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Segments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SegmentAssociatedFeatureState'
          description: ''
  /api/v1/projects/{project_pk}/segments/{id}/clone/:
    post:
      operationId: api_v1_projects_segments_clone_create
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this segment.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Segments
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CloneSegment'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CloneSegment'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CloneSegment'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Segment'
          description: ''
  /api/v1/projects/{project_pk}/tags/:
    get:
      operationId: api_v1_projects_tags_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedTagList'
          description: ''
    post:
      operationId: api_v1_projects_tags_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Tag'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Tag'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Tag'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tag'
          description: ''
  /api/v1/projects/{project_pk}/tags/{id}/:
    get:
      operationId: api_v1_projects_tags_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this tag.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tag'
          description: ''
    put:
      operationId: api_v1_projects_tags_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this tag.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Tag'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Tag'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Tag'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tag'
          description: ''
    patch:
      operationId: api_v1_projects_tags_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this tag.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedTag'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedTag'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedTag'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tag'
          description: ''
    delete:
      operationId: api_v1_projects_tags_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this tag.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/tags/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_projects_tags_get_by_uuid_retrieve
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      - in: path
        name: uuid
        schema:
          type: string
          pattern: ^[0-9a-f-]+$
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tag'
          description: ''
  /api/v1/projects/{project_pk}/user-group-permissions/:
    get:
      operationId: api_v1_projects_user_group_permissions_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ListUserPermissionGroupProjectPermission'
          description: ''
    post:
      operationId: api_v1_projects_user_group_permissions_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          description: ''
  /api/v1/projects/{project_pk}/user-group-permissions/{id}/:
    get:
      operationId: api_v1_projects_user_group_permissions_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          description: ''
    put:
      operationId: api_v1_projects_user_group_permissions_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          description: ''
    patch:
      operationId: api_v1_projects_user_group_permissions_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserPermissionGroupProjectPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserPermissionGroupProjectPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserPermissionGroupProjectPermission'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserPermissionGroupProjectPermission'
          description: ''
    delete:
      operationId: api_v1_projects_user_group_permissions_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/{project_pk}/user-permissions/:
    get:
      operationId: api_v1_projects_user_permissions_list
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ListUserProjectPermission'
          description: ''
    post:
      operationId: api_v1_projects_user_permissions_create
      parameters:
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          description: ''
  /api/v1/projects/{project_pk}/user-permissions/{id}/:
    get:
      operationId: api_v1_projects_user_permissions_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          description: ''
    put:
      operationId: api_v1_projects_user_permissions_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          description: ''
    patch:
      operationId: api_v1_projects_user_permissions_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserProjectPermission'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserProjectPermission'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCreateUpdateUserProjectPermission'
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateUpdateUserProjectPermission'
          description: ''
    delete:
      operationId: api_v1_projects_user_permissions_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this user project permission.
        required: true
      - in: path
        name: project_pk
        schema:
          type: integer
        required: true
      tags:
      - Permissions
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '204':
          description: No response body
  /api/v1/projects/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_projects_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          pattern: ^[0-9a-f-]+$
        required: true
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectList'
          description: ''
  /api/v1/projects/permissions/:
    get:
      operationId: api_v1_projects_permissions_list
      tags:
      - Projects
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PermissionModel'
          description: ''
  /api/v1/segments/get-by-uuid/{uuid}/:
    get:
      operationId: api_v1_segments_get_by_uuid_retrieve
      parameters:
      - in: path
        name: uuid
        schema:
          type: string
          format: uuid
        required: true
      tags:
      - Segments
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Segment'
          description: ''
  /api/v1/traits/:
    post:
      operationId: api_v1_traits_create
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SDKCreateUpdateTrait'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SDKCreateUpdateTrait'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SDKCreateUpdateTrait'
        required: true
      security:
      - Environment API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SDKCreateUpdateTrait'
          description: ''
  /api/v1/traits/bulk/:
    put:
      operationId: api_v1_traits_bulk_update
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/SDKCreateUpdateTrait'
          application/x-www-form-urlencoded:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/SDKCreateUpdateTrait'
          multipart/form-data:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/SDKCreateUpdateTrait'
        required: true
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SDKBulkCreateUpdateTrait'
          description: ''
  /api/v1/traits/increment-value/:
    post:
      operationId: api_v1_traits_increment_value_create
      tags:
      - Identities
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/IncrementTraitValue'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/IncrementTraitValue'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/IncrementTraitValue'
        required: true
      security:
      - Environment API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/IncrementTraitValue'
          description: ''
  /api/v1/users/join/{hash}/:
    post:
      operationId: api_v1_users_join_create
      parameters:
      - in: path
        name: hash
        schema:
          type: string
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/users/join/link/{hash}/:
    post:
      operationId: api_v1_users_join_link_create
      parameters:
      - in: path
        name: hash
        schema:
          type: string
        required: true
      tags:
      - Authentication
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          description: No response body
  /api/v1/webhooks/test/:
    post:
      operationId: api_v1_webhooks_test_create
      tags:
      - Webhooks
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TestWebhook'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/TestWebhook'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/TestWebhook'
        required: true
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestWebhookSuccessResponse'
          description: ''
        '400':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestWebhookErrorResponse'
          description: ''
  /api/v2/analytics/flags/:
    post:
      operationId: api_v2_analytics_flags_create
      tags:
      - Analytics
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SDKAnalyticsFlags'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/SDKAnalyticsFlags'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/SDKAnalyticsFlags'
        required: true
      security:
      - Environment API Key: []
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SDKAnalyticsFlags'
          description: ''
  /o/register/:
    post:
      operationId: o_register_create
      description: RFC 7591 Dynamic Client Registration endpoint.
      tags:
      - o
      security:
      - {}
      responses:
        '200':
          description: No response body
  /processor/monitoring/:
    get:
      operationId: processor_monitoring_retrieve
      tags:
      - processor
      security:
      - tokenAuth: []
      - Master API Key: []
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Monitoring'
          description: ''
components:
  schemas:
    Activation:
      type: object
      properties:
        uid:
          type: string
        token:
          type: string
      required:
      - token
      - uid
    AmplitudeConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
        base_url:
          type: string
          format: uri
          maxLength: 200
      required:
      - api_key
    AuditLogList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        created_date:
          type: string
          format: date-time
          title: DateCreated
        log:
          type: string
        author:
          $ref: '#/components/schemas/UserList'
        environment:
          $ref: '#/components/schemas/EnvironmentSerializerLight'
        project:
          $ref: '#/components/schemas/ProjectList'
        related_object_id:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        related_object_uuid:
          type:
          - string
          - 'null'
          maxLength: 36
        related_object_type:
          type:
          - string
          - 'null'
          maxLength: 20
        is_system_event:
          type: boolean
      required:
      - author
      - created_date
      - environment
      - log
      - project
    AuditLogRetrieve:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        created_date:
          type: string
          format: date-time
          title: DateCreated
        log:
          type: string
        author:
          $ref: '#/components/schemas/UserList'
        environment:
          $ref: '#/components/schemas/EnvironmentSerializerLight'
        project:
          $ref: '#/components/schemas/ProjectList'
        related_object_id:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        related_object_uuid:
          type:
          - string
          - 'null'
          maxLength: 36
        related_object_type:
          type:
          - string
          - 'null'
          maxLength: 20
        is_system_event:
          type: boolean
        change_details:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              old:
                type:
                - string
                - number
                - boolean
                - 'null'
              new:
                type:
                - string
                - number
                - boolean
                - 'null'
          readOnly: true
        change_type:
          allOf:
          - $ref: '#/components/schemas/ChangeTypeEnum'
          readOnly: true
      required:
      - author
      - created_date
      - environment
      - log
      - project
    BaseEdgeIdentityFeatureState:
      type: object
      properties:
        feature_state_value:
          type:
          - string
          - integer
          - boolean
          - 'null'
          description: Feature state value (string, integer, or boolean)
        feature:
          type: integer
          description: Feature ID
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/EdgeMultivariateFeatureStateValue'
        enabled:
          type: boolean
          default: false
        featurestate_uuid:
          type: string
          readOnly: true
      required:
      - feature
    BaseUrlEnum:
      enum:
      - https://api.segment.io/
      - https://events.eu1.segmentapis.com/
      type: string
      description: |-
        * `https://api.segment.io/` - https://api.segment.io/
        * `https://events.eu1.segmentapis.com/` - https://events.eu1.segmentapis.com/
    BillingStatusEnum:
      enum:
      - ACTIVE
      - DUNNING
      type: string
      description: |-
        * `ACTIVE` - Active
        * `DUNNING` - Dunning
    BlankEnum:
      enum:
      - ''
    ChangeTypeEnum:
      enum:
      - CREATE
      - UPDATE
      - DELETE
      - UNKNOWN
      type: string
    CloneEnvironment:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          readOnly: true
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        clone_feature_states_async:
          type: boolean
          writeOnly: true
          default: false
          description: 'If True, the environment will be created immediately, but
            the feature states will be created asynchronously. Environment will have
            `is_creating: true` until this process is completed.'
      required:
      - name
    CloneSegment:
      type: object
      properties:
        name:
          type: string
          maxLength: 2000
      required:
      - name
    Condition:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        operator:
          $ref: '#/components/schemas/ConditionOperatorEnum'
        property:
          type:
          - string
          - 'null'
          maxLength: 1000
        value:
          type:
          - string
          - 'null'
          maxLength: 1000
        description:
          type:
          - string
          - 'null'
        delete:
          type: boolean
          writeOnly: true
      required:
      - operator
    ConditionOperatorEnum:
      enum:
      - EQUAL
      - GREATER_THAN
      - LESS_THAN
      - CONTAINS
      - GREATER_THAN_INCLUSIVE
      - LESS_THAN_INCLUSIVE
      - NOT_CONTAINS
      - NOT_EQUAL
      - REGEX
      - PERCENTAGE_SPLIT
      - MODULO
      - IS_SET
      - IS_NOT_SET
      - IN
      type: string
      description: |-
        * `EQUAL` - Exactly Matches
        * `GREATER_THAN` - Greater than
        * `LESS_THAN` - Less than
        * `CONTAINS` - Contains
        * `GREATER_THAN_INCLUSIVE` - Greater than or equal to
        * `LESS_THAN_INCLUSIVE` - Less than or equal to
        * `NOT_CONTAINS` - Does not contain
        * `NOT_EQUAL` - Does not match
        * `REGEX` - Matches regex
        * `PERCENTAGE_SPLIT` - Percentage split
        * `MODULO` - Modulo Operation
        * `IS_SET` - Is set
        * `IS_NOT_SET` - Is not set
        * `IN` - In
    ContentType:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        app_label:
          type: string
          maxLength: 100
        model:
          type: string
          title: Python model class name
          maxLength: 100
      required:
      - app_label
      - model
    CreateEnvironment:
      type: object
      description: |-
        Mixin to add read only status to fields in a given serializer based on the existence
        of a subscription and a black list of plan ids

        Example usage:

            class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
                class Meta:
                    model = MyModel
                    fields = ("my_field",)

                invalid_plans = ("free",)
                field_names = ("my_field",)

                def get_subscription(self):
                    return subscription
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          maxLength: 100
        description:
          type:
          - string
          - 'null'
          maxLength: 20000
        project:
          type: integer
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
          readOnly: true
        allow_client_traits:
          type: boolean
          description: Allows clients using the client API key to set traits.
        banner_text:
          type:
          - string
          - 'null'
          maxLength: 255
        banner_colour:
          type:
          - string
          - 'null'
          description: hex code for the banner colour
          maxLength: 7
        hide_disabled_flags:
          type:
          - boolean
          - 'null'
          description: 'If true will exclude flags from SDK which are disabled. NOTE:
            If set, this will override the project `hide_disabled_flags`'
        use_mv_v2_evaluation:
          type: boolean
          description: |-
            To avoid breaking the API, we return this field as well.

            Warning: this will still mean that sending the `use_mv_v2_evaluation` field
            (e.g. in a PUT request) will not behave as expected but, since this is a minor
            issue, I think we can ignore.
          readOnly: true
        use_identity_composite_key_for_hashing:
          type: boolean
          description: Enable this to have consistent multivariate and percentage
            split evaluations across all SDKs (in local and server side mode)
        hide_sensitive_data:
          type: boolean
          description: 'If true, will hide sensitive data(e.g: traits, description
            etc) from the SDK endpoints'
        use_v2_feature_versioning:
          type: boolean
          readOnly: true
        use_identity_overrides_in_local_eval:
          type: boolean
          description: When enabled, identity overrides will be included in the environment
            document
        is_creating:
          type: boolean
          readOnly: true
          description: Attribute used to indicate when an environment is still being
            created (via clone for example)
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
      required:
      - name
      - project
    CreateFeature:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 2000
        type:
          oneOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          - $ref: '#/components/schemas/BlankEnum'
        default_enabled:
          type: boolean
        initial_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        description:
          type:
          - string
          - 'null'
        tags:
          type: array
          items:
            type: integer
        multivariate_options:
          type: array
          items:
            $ref: '#/components/schemas/NestedMultivariateFeatureOption'
        is_archived:
          type: boolean
        owners:
          type: array
          items:
            type: integer
        group_owners:
          type: array
          items:
            type: integer
        uuid:
          type: string
          format: uuid
          readOnly: true
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        environment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        segment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        num_segment_overrides:
          type: integer
          readOnly: true
          description: Number of segment overrides that exist for the given feature
            in the environment provided by the `environment` query parameter.
        num_identity_overrides:
          type:
          - integer
          - 'null'
          readOnly: true
          description: 'Number of identity overrides that exist for the given feature
            in the environment provided by the `environment` query parameter. Note:
            will return null for Edge enabled projects.'
        is_num_identity_overrides_complete:
          type: boolean
          readOnly: true
          default: true
        is_server_key_only:
          type: boolean
        last_modified_in_any_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the given project. Note: requires feature versioning
            v2 enabled on the environment.'
        last_modified_in_current_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the current environment. Note: requires that the
            environment query parameter is passed and feature versioning v2 enabled
            on the environment.'
      required:
      - name
    CreateFeatureExport:
      type: object
      properties:
        environment_id:
          type: integer
        tag_ids:
          type: array
          items:
            type: integer
      required:
      - environment_id
      - tag_ids
    CreateFeatureHealthProvider:
      type: object
      properties:
        name:
          $ref: '#/components/schemas/NameEnum'
      required:
      - name
    CreateLaunchDarklyImportRequest:
      type: object
      properties:
        token:
          type: string
        project_key:
          type: string
      required:
      - project_key
      - token
    CreateUpdateUserEnvironmentPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        user:
          type: integer
      required:
      - user
    CreateUpdateUserPermissionGroupEnvironmentPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        group:
          type: integer
      required:
      - group
    CreateUpdateUserPermissionGroupProjectPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        group:
          type: integer
      required:
      - group
    CreateUpdateUserProjectPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        user:
          type: integer
      required:
      - user
    CustomCreateSegmentOverrideFeatureSegment:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        segment:
          type: integer
        priority:
          type: integer
          minimum: 0
        uuid:
          type: string
          format: uuid
          readOnly: true
      required:
      - segment
    CustomCreateSegmentOverrideFeatureState:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature:
          type: integer
          readOnly: true
        enabled:
          type: boolean
        feature_state_value:
          $ref: '#/components/schemas/FeatureStateValue'
        feature_segment:
          oneOf:
          - $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureSegment'
          - type: 'null'
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        environment:
          type:
          - integer
          - 'null'
          readOnly: true
        identity:
          type:
          - integer
          - 'null'
          readOnly: true
        change_request:
          type:
          - integer
          - 'null'
          readOnly: true
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
      required:
      - feature_state_value
    CustomCurrentUser:
      type: object
      properties:
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        sign_up_type:
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          readOnly: true
        auth_type:
          type: string
          readOnly: true
        is_superuser:
          type: boolean
          readOnly: true
        date_joined:
          type: string
          format: date-time
        uuid:
          type: string
          format: uuid
          readOnly: true
        pylon_email_signature:
          type: string
          readOnly: true
      required:
      - first_name
      - last_name
    CustomEnvironmentFeatureVersionFeatureState:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature:
          type: integer
          readOnly: true
        enabled:
          type: boolean
        feature_state_value:
          $ref: '#/components/schemas/FeatureStateValue'
        feature_segment:
          oneOf:
          - $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureSegment'
          - type: 'null'
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        environment:
          type:
          - integer
          - 'null'
          readOnly: true
        identity:
          type:
          - integer
          - 'null'
          readOnly: true
        change_request:
          type:
          - integer
          - 'null'
          readOnly: true
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
      required:
      - feature_state_value
    CustomToken:
      type: object
      properties:
        key:
          type: string
          maxLength: 40
      required:
      - key
    CustomUserCreate:
      type: object
      properties:
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        sign_up_type:
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        email:
          type: string
          format: email
          maxLength: 254
        id:
          type: integer
          readOnly: true
        password:
          type: string
          writeOnly: true
        is_active:
          type: boolean
          readOnly: true
          title: Active
          description: Designates whether this user should be treated as active. Unselect
            this instead of deleting accounts.
        marketing_consent_given:
          type: boolean
          readOnly: true
          description: Determines whether the user has agreed to receive marketing
            mails
        uuid:
          type: string
          format: uuid
          readOnly: true
        key:
          type: string
          readOnly: true
        superuser:
          type: boolean
          writeOnly: true
      required:
      - email
      - first_name
      - last_name
      - password
    DataDogConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type: string
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
        use_custom_source:
          type: boolean
      required:
      - api_key
      - base_url
    DeleteAllTraitKeys:
      type: object
      properties:
        key:
          type: string
      required:
      - key
    DeleteSegmentOverride:
      type: object
      properties:
        feature:
          $ref: '#/components/schemas/FeatureIdentifier'
        segment:
          $ref: '#/components/schemas/SegmentIdentifier'
      required:
      - feature
      - segment
    DerivedFrom:
      type: object
      properties:
        groups:
          type: array
          items:
            $ref: '#/components/schemas/Group'
        roles:
          type: array
          items:
            $ref: '#/components/schemas/PermissionRole'
      required:
      - groups
      - roles
    DetailedPermissions:
      type: object
      properties:
        permission_key:
          type: string
        is_directly_granted:
          type: boolean
        derived_from:
          $ref: '#/components/schemas/DerivedFrom'
      required:
      - derived_from
      - is_directly_granted
      - permission_key
    DynatraceConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
        entity_selector:
          type: string
          maxLength: 1000
      required:
      - api_key
      - entity_selector
    EdgeIdentity:
      type: object
      properties:
        identity_uuid:
          type: string
          readOnly: true
        identifier:
          type: string
          maxLength: 2000
        dashboard_alias:
          type: string
          maxLength: 100
      required:
      - identifier
    EdgeIdentityFeatureState:
      type: object
      properties:
        feature_state_value:
          type:
          - string
          - integer
          - boolean
          - 'null'
          description: Feature state value (string, integer, or boolean)
        feature:
          type: integer
          description: Feature ID
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/EdgeMultivariateFeatureStateValue'
        enabled:
          type: boolean
          default: false
        featurestate_uuid:
          type: string
          readOnly: true
        identity_uuid:
          type: string
          format: uuid
          readOnly: true
      required:
      - feature
    EdgeIdentitySourceIdentityRequest:
      type: object
      properties:
        source_identity_uuid:
          type: string
          description: UUID of the source identity to clone feature states from.
      required:
      - source_identity_uuid
    EdgeIdentityTraits:
      type: object
      properties:
        trait_key:
          type: string
        trait_value:
          type:
          - string
          - 'null'
      required:
      - trait_key
      - trait_value
    EdgeIdentityUpdate:
      type: object
      properties:
        identity_uuid:
          type: string
          readOnly: true
        identifier:
          type: string
          readOnly: true
          maxLength: 2000
        dashboard_alias:
          type: string
          maxLength: 100
      required:
      - identifier
    EdgeIdentityWithIdentifierFeatureStateRequestBody:
      type: object
      properties:
        feature_state_value:
          type:
          - string
          - integer
          - boolean
          - 'null'
          description: Feature state value (string, integer, or boolean)
        feature:
          oneOf:
          - type: integer
            description: Feature ID
          - type: string
            description: Feature name
          description: Feature identifier (ID or name)
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/EdgeMultivariateFeatureStateValue'
        enabled:
          type: boolean
          default: false
        featurestate_uuid:
          type: string
          readOnly: true
        identity_uuid:
          type: string
          format: uuid
          readOnly: true
        identifier:
          type: string
          maxLength: 2000
      required:
      - feature
      - identifier
    EdgeMultivariateFeatureStateValue:
      type: object
      properties:
        multivariate_feature_option:
          type: integer
        percentage_allocation:
          type: number
          format: double
          maximum: 100
          minimum: 0
      required:
      - multivariate_feature_option
      - percentage_allocation
    EdgeV2MigrationStatusEnum:
      enum:
      - NOT_STARTED
      - IN_PROGRESS
      - COMPLETE
      - INCOMPLETE
      type: string
      description: |-
        * `NOT_STARTED` - Not Started
        * `IN_PROGRESS` - In Progress
        * `COMPLETE` - Complete
        * `INCOMPLETE` - Incomplete (identity overrides skipped)
    EnvironmentAPIKey:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        key:
          type: string
          readOnly: true
        active:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        name:
          type: string
          maxLength: 100
        expires_at:
          type:
          - string
          - 'null'
          format: date-time
      required:
      - name
    EnvironmentDefault:
      type: object
      properties:
        enabled:
          type: boolean
        value:
          $ref: '#/components/schemas/FeatureValue'
      required:
      - enabled
      - value
    EnvironmentFeatureVersion:
      type: object
      properties:
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        published:
          type: boolean
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        uuid:
          type: string
          format: uuid
          readOnly: true
        is_live:
          type: boolean
          readOnly: true
        published_by:
          type:
          - integer
          - 'null'
          readOnly: true
        created_by:
          type:
          - integer
          - 'null'
          readOnly: true
        description:
          type:
          - string
          - 'null'
    EnvironmentFeatureVersionCreate:
      type: object
      properties:
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        published:
          type: boolean
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        uuid:
          type: string
          format: uuid
          readOnly: true
        is_live:
          type: boolean
          readOnly: true
        published_by:
          type:
          - integer
          - 'null'
          readOnly: true
        created_by:
          type:
          - integer
          - 'null'
          readOnly: true
        description:
          type:
          - string
          - 'null'
        feature_states_to_create:
          type:
          - array
          - 'null'
          items:
            $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          writeOnly: true
          description: 'Array of feature states that will be created in the new version.
            Note: these can only include segment overrides.'
        feature_states_to_update:
          type:
          - array
          - 'null'
          items:
            $ref: '#/components/schemas/CustomEnvironmentFeatureVersionFeatureState'
          writeOnly: true
          description: Array of feature states to update in the new version.
        segment_ids_to_delete_overrides:
          type:
          - array
          - 'null'
          items:
            type: integer
          writeOnly: true
          description: List of segment ids for which the segment overrides will be
            removed in the new version.
        publish_immediately:
          type: boolean
          writeOnly: true
          default: false
          description: Boolean to confirm whether the new version should be publish
            immediately or not.
    EnvironmentFeatureVersionPublish:
      type: object
      properties:
        live_from:
          type: string
          format: date-time
    EnvironmentFeatureVersionRetrieve:
      type: object
      properties:
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        published:
          type: boolean
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        uuid:
          type: string
          format: uuid
          readOnly: true
        is_live:
          type: boolean
          readOnly: true
        published_by:
          type:
          - integer
          - 'null'
          readOnly: true
        created_by:
          type:
          - integer
          - 'null'
          readOnly: true
        description:
          type:
          - string
          - 'null'
        previous_version_uuid:
          type:
          - string
          - 'null'
          readOnly: true
        feature:
          type: integer
          readOnly: true
        environment:
          type: integer
          readOnly: true
    EnvironmentMetrics:
      type: object
      properties:
        metrics:
          type: array
          items:
            $ref: '#/components/schemas/MetricItem'
          readOnly: true
    EnvironmentRetrieveSerializerWithMetadata:
      type: object
      description: Functionality for serializers that need to handle metadata
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          maxLength: 100
        description:
          type:
          - string
          - 'null'
          maxLength: 20000
        project:
          type: integer
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        allow_client_traits:
          type: boolean
          description: Allows clients using the client API key to set traits.
        banner_text:
          type:
          - string
          - 'null'
          maxLength: 255
        banner_colour:
          type:
          - string
          - 'null'
          description: hex code for the banner colour
          maxLength: 7
        hide_disabled_flags:
          type:
          - boolean
          - 'null'
          description: 'If true will exclude flags from SDK which are disabled. NOTE:
            If set, this will override the project `hide_disabled_flags`'
        use_mv_v2_evaluation:
          type: boolean
          description: |-
            To avoid breaking the API, we return this field as well.

            Warning: this will still mean that sending the `use_mv_v2_evaluation` field
            (e.g. in a PUT request) will not behave as expected but, since this is a minor
            issue, I think we can ignore.
          readOnly: true
        use_identity_composite_key_for_hashing:
          type: boolean
          description: Enable this to have consistent multivariate and percentage
            split evaluations across all SDKs (in local and server side mode)
        hide_sensitive_data:
          type: boolean
          description: 'If true, will hide sensitive data(e.g: traits, description
            etc) from the SDK endpoints'
        use_v2_feature_versioning:
          type: boolean
          readOnly: true
        use_identity_overrides_in_local_eval:
          type: boolean
          description: When enabled, identity overrides will be included in the environment
            document
        is_creating:
          type: boolean
          readOnly: true
          description: Attribute used to indicate when an environment is still being
            created (via clone for example)
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
        total_segment_overrides:
          type: integer
      required:
      - name
      - project
      - total_segment_overrides
    EnvironmentSerializerLight:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          maxLength: 100
        description:
          type:
          - string
          - 'null'
          maxLength: 20000
        project:
          type: integer
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        allow_client_traits:
          type: boolean
          description: Allows clients using the client API key to set traits.
        banner_text:
          type:
          - string
          - 'null'
          maxLength: 255
        banner_colour:
          type:
          - string
          - 'null'
          description: hex code for the banner colour
          maxLength: 7
        hide_disabled_flags:
          type:
          - boolean
          - 'null'
          description: 'If true will exclude flags from SDK which are disabled. NOTE:
            If set, this will override the project `hide_disabled_flags`'
        use_mv_v2_evaluation:
          type: boolean
          description: |-
            To avoid breaking the API, we return this field as well.

            Warning: this will still mean that sending the `use_mv_v2_evaluation` field
            (e.g. in a PUT request) will not behave as expected but, since this is a minor
            issue, I think we can ignore.
          readOnly: true
        use_identity_composite_key_for_hashing:
          type: boolean
          description: Enable this to have consistent multivariate and percentage
            split evaluations across all SDKs (in local and server side mode)
        hide_sensitive_data:
          type: boolean
          description: 'If true, will hide sensitive data(e.g: traits, description
            etc) from the SDK endpoints'
        use_v2_feature_versioning:
          type: boolean
          readOnly: true
        use_identity_overrides_in_local_eval:
          type: boolean
          description: When enabled, identity overrides will be included in the environment
            document
        is_creating:
          type: boolean
          readOnly: true
          description: Attribute used to indicate when an environment is still being
            created (via clone for example)
      required:
      - name
      - project
    EnvironmentSerializerWithMetadata:
      type: object
      description: Functionality for serializers that need to handle metadata
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          maxLength: 100
        description:
          type:
          - string
          - 'null'
          maxLength: 20000
        project:
          type: integer
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        allow_client_traits:
          type: boolean
          description: Allows clients using the client API key to set traits.
        banner_text:
          type:
          - string
          - 'null'
          maxLength: 255
        banner_colour:
          type:
          - string
          - 'null'
          description: hex code for the banner colour
          maxLength: 7
        hide_disabled_flags:
          type:
          - boolean
          - 'null'
          description: 'If true will exclude flags from SDK which are disabled. NOTE:
            If set, this will override the project `hide_disabled_flags`'
        use_mv_v2_evaluation:
          type: boolean
          description: |-
            To avoid breaking the API, we return this field as well.

            Warning: this will still mean that sending the `use_mv_v2_evaluation` field
            (e.g. in a PUT request) will not behave as expected but, since this is a minor
            issue, I think we can ignore.
          readOnly: true
        use_identity_composite_key_for_hashing:
          type: boolean
          description: Enable this to have consistent multivariate and percentage
            split evaluations across all SDKs (in local and server side mode)
        hide_sensitive_data:
          type: boolean
          description: 'If true, will hide sensitive data(e.g: traits, description
            etc) from the SDK endpoints'
        use_v2_feature_versioning:
          type: boolean
          readOnly: true
        use_identity_overrides_in_local_eval:
          type: boolean
          description: When enabled, identity overrides will be included in the environment
            document
        is_creating:
          type: boolean
          readOnly: true
          description: Attribute used to indicate when an environment is still being
            created (via clone for example)
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
      required:
      - name
      - project
    Error:
      type: object
      properties:
        message:
          type: string
      required:
      - message
    ExperimentResults:
      type: object
      description: Serializer for the full experiment results response.
      properties:
        feature:
          type: string
        variants:
          type: array
          items:
            $ref: '#/components/schemas/ExperimentVariantResult'
        statistics:
          $ref: '#/components/schemas/ExperimentStatistics'
      required:
      - feature
      - statistics
      - variants
    ExperimentStatistics:
      type: object
      description: Serializer for statistical analysis results.
      properties:
        p_value:
          type: number
          format: double
        significant:
          type: boolean
        chance_to_win:
          type: object
          additionalProperties:
            type: number
            format: double
        lift:
          type: string
        winner:
          type:
          - string
          - 'null'
        recommendation:
          type: string
        sample_size_warning:
          type:
          - string
          - 'null'
      required:
      - chance_to_win
      - lift
      - p_value
      - recommendation
      - significant
      - winner
    ExperimentVariantResult:
      type: object
      description: Serializer for individual variant results.
      properties:
        variant:
          type: string
        evaluations:
          type: integer
        conversions:
          type: integer
        conversion_rate:
          type: number
          format: double
      required:
      - conversion_rate
      - conversions
      - evaluations
      - variant
    FeatureEvaluationData:
      type: object
      properties:
        day:
          type: string
        count:
          type: integer
        labels:
          oneOf:
          - $ref: '#/components/schemas/Labels'
          - type: 'null'
      required:
      - count
      - day
      - labels
    FeatureExport:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          readOnly: true
        environment_id:
          type: integer
          readOnly: true
        status:
          $ref: '#/components/schemas/Status6d4Enum'
        created_at:
          type: string
          format: date-time
          readOnly: true
    FeatureExternalResource:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          format: uri
          maxLength: 200
        type:
          $ref: '#/components/schemas/FeatureExternalResourceTypeEnum'
        metadata:
          oneOf:
          - {}
          - type: 'null'
        feature:
          type: integer
      required:
      - feature
      - type
      - url
    FeatureExternalResourceTypeEnum:
      enum:
      - GITHUB_ISSUE
      - GITHUB_PR
      - GITLAB_ISSUE
      - GITLAB_MR
      type: string
      description: |-
        * `GITHUB_ISSUE` - GitHub Issue
        * `GITHUB_PR` - GitHub PR
        * `GITLAB_ISSUE` - GitLab Issue
        * `GITLAB_MR` - GitLab MR
    FeatureFlagCodeReferencesRepositoryCount:
      type: object
      properties:
        repository_url:
          type: string
          format: uri
        count:
          type: integer
        last_successful_repository_scanned_at:
          type: string
          format: date-time
        last_feature_found_at:
          type:
          - string
          - 'null'
          format: date-time
      required:
      - count
      - last_feature_found_at
      - last_successful_repository_scanned_at
      - repository_url
    FeatureFlagCodeReferencesRepositorySummary:
      type: object
      properties:
        repository_url:
          type: string
          format: uri
        vcs_provider:
          $ref: '#/components/schemas/VcsProviderEnum'
        revision:
          type: string
        last_successful_repository_scanned_at:
          type: string
          format: date-time
        last_feature_found_at:
          type:
          - string
          - 'null'
          format: date-time
        code_references:
          type: array
          items:
            $ref: '#/components/schemas/_CodeReferenceDetail'
      required:
      - code_references
      - last_feature_found_at
      - last_successful_repository_scanned_at
      - repository_url
      - revision
      - vcs_provider
    FeatureFlagCodeReferencesScan:
      type: object
      properties:
        created_at:
          type: string
          format: date-time
          readOnly: true
        project:
          type: integer
          readOnly: true
        repository_url:
          type: string
          format: uri
        vcs_provider:
          allOf:
          - $ref: '#/components/schemas/VcsProviderEnum'
          default: github
        revision:
          type: string
          maxLength: 100
        code_references:
          type: array
          items:
            $ref: '#/components/schemas/_CodeReferenceSubmit'
      required:
      - code_references
      - repository_url
      - revision
    FeatureGroupOwnerInput:
      type: object
      properties:
        group_ids:
          type: array
          items:
            type: integer
      required:
      - group_ids
    FeatureHealthEvent:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
        environment:
          type:
          - integer
          - 'null'
          readOnly: true
        feature:
          type: integer
          readOnly: true
        provider_name:
          type:
          - string
          - 'null'
          readOnly: true
        reason:
          oneOf:
          - $ref: '#/components/schemas/FeatureHealthEventReason'
          - type: 'null'
        type:
          allOf:
          - $ref: '#/components/schemas/FeatureHealthEventTypeEnum'
          readOnly: true
      required:
      - reason
    FeatureHealthEventReason:
      type: object
      properties:
        text_blocks:
          type: array
          items:
            $ref: '#/components/schemas/FeatureHealthEventReasonTextBlock'
        url_blocks:
          type: array
          items:
            $ref: '#/components/schemas/FeatureHealthEventReasonUrlBlock'
      required:
      - text_blocks
      - url_blocks
    FeatureHealthEventReasonTextBlock:
      type: object
      properties:
        text:
          type: string
        title:
          type: string
      required:
      - text
    FeatureHealthEventReasonUrlBlock:
      type: object
      properties:
        url:
          type: string
        title:
          type: string
      required:
      - url
    FeatureHealthEventTypeEnum:
      enum:
      - UNHEALTHY
      - HEALTHY
      type: string
      description: |-
        * `UNHEALTHY` - Unhealthy
        * `HEALTHY` - Healthy
    FeatureHealthProvider:
      type: object
      properties:
        created_by:
          type: string
          format: email
          readOnly: true
        name:
          $ref: '#/components/schemas/NameEnum'
        project:
          type: integer
        webhook_url:
          type: string
          readOnly: true
      required:
      - name
      - project
    FeatureIdentifier:
      type: object
      properties:
        name:
          type: string
        id:
          type: integer
    FeatureImport:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        environment_id:
          type: integer
          readOnly: true
        strategy:
          $ref: '#/components/schemas/FeatureImportStrategyEnum'
        status:
          $ref: '#/components/schemas/Status6d4Enum'
        created_at:
          type: string
          format: date-time
          readOnly: true
      required:
      - strategy
    FeatureImportStrategyEnum:
      enum:
      - SKIP
      - OVERWRITE_DESTRUCTIVE
      type: string
      description: |-
        * `SKIP` - Skip
        * `OVERWRITE_DESTRUCTIVE` - Overwrite Destructive
    FeatureImportUpload:
      type: object
      properties:
        file:
          type: string
          format: uri
        strategy:
          $ref: '#/components/schemas/FeatureImportUploadStrategyEnum'
      required:
      - file
      - strategy
    FeatureImportUploadStrategyEnum:
      enum:
      - SKIP
      - OVERWRITE_DESTRUCTIVE
      type: string
      description: |-
        * `SKIP` - SKIP
        * `OVERWRITE_DESTRUCTIVE` - OVERWRITE_DESTRUCTIVE
    FeatureInfluxData:
      type: object
      properties:
        events_list:
          type: array
          items:
            type: object
            additionalProperties: {}
      required:
      - events_list
    FeatureMVOptionsValuesResponse:
      type: object
      properties:
        control_value:
          oneOf:
          - type: string
          - type: integer
          - type: boolean
          - type: 'null'
          readOnly: true
        options:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateOptionValues'
      required:
      - options
    FeatureOwnerInput:
      type: object
      properties:
        user_ids:
          type: array
          items:
            type: integer
      required:
      - user_ids
    FeatureSegmentChangePriorities:
      type: object
      properties:
        id:
          type: integer
        priority:
          type: integer
          minimum: 0
          description: Value to change the feature segment's priority to.
      required:
      - id
      - priority
    FeatureSegmentCreate:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        feature:
          type: integer
        segment:
          type: integer
        environment:
          type: integer
        priority:
          type: integer
          readOnly: true
      required:
      - environment
      - feature
      - segment
    FeatureSegmentList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        segment:
          type: integer
          readOnly: true
        priority:
          type: integer
          readOnly: true
        environment:
          type: integer
          readOnly: true
        segment_name:
          type: string
          readOnly: true
        is_feature_specific:
          type: boolean
          readOnly: true
    FeatureStateSerializerBasic:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature_state_value:
          type:
          - string
          - integer
          - number
          - boolean
          - 'null'
          readOnly: true
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
        identifier:
          type: string
          description: Can be passed as an alternative to `identity`
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        enabled:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        version:
          type:
          - integer
          - 'null'
          readOnly: true
        feature:
          type: integer
        environment:
          type:
          - integer
          - 'null'
        identity:
          type:
          - integer
          - 'null'
        feature_segment:
          type:
          - integer
          - 'null'
        change_request:
          type:
          - integer
          - 'null'
        environment_feature_version:
          type:
          - string
          - 'null'
          format: uuid
      required:
      - feature
    FeatureStateSerializerCreate:
      type: object
      properties:
        feature:
          type: integer
        enabled:
          type: boolean
      required:
      - feature
    FeatureStateSerializerSmall:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        feature_state_value:
          type:
          - string
          - integer
          - boolean
          - 'null'
          readOnly: true
        environment:
          type:
          - integer
          - 'null'
        identity:
          type:
          - integer
          - 'null'
        feature_segment:
          type:
          - integer
          - 'null'
        enabled:
          type: boolean
    FeatureStateSerializerWithIdentity:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature_state_value:
          type:
          - string
          - integer
          - number
          - boolean
          - 'null'
          readOnly: true
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
        identifier:
          type: string
          description: Can be passed as an alternative to `identity`
        identity:
          $ref: '#/components/schemas/_Identity'
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        enabled:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        version:
          type:
          - integer
          - 'null'
          readOnly: true
        feature:
          type: integer
        environment:
          type:
          - integer
          - 'null'
        feature_segment:
          type:
          - integer
          - 'null'
        change_request:
          type:
          - integer
          - 'null'
        environment_feature_version:
          type:
          - string
          - 'null'
          format: uuid
      required:
      - feature
      - identity
    FeatureStateValue:
      type: object
      properties:
        type:
          oneOf:
          - $ref: '#/components/schemas/Type975Enum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        string_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        integer_value:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        boolean_value:
          type:
          - boolean
          - 'null'
    FeatureUpdateSegmentData:
      type: object
      properties:
        id:
          type: integer
        priority:
          type:
          - integer
          - 'null'
      required:
      - id
    FeatureValue:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/FeatureValueTypeEnum'
        value:
          type: string
      required:
      - type
      - value
    FeatureValueTypeEnum:
      enum:
      - integer
      - string
      - boolean
      type: string
      description: |-
        * `integer` - integer
        * `string` - string
        * `boolean` - boolean
    GetEdgeIdentityOverrides:
      type: object
      properties:
        results:
          type: array
          items:
            $ref: '#/components/schemas/GetEdgeIdentityOverridesResult'
      required:
      - results
    GetEdgeIdentityOverridesResult:
      type: object
      properties:
        identifier:
          type: string
        identity_uuid:
          type: string
        feature_state:
          $ref: '#/components/schemas/BaseEdgeIdentityFeatureState'
      required:
      - feature_state
      - identifier
      - identity_uuid
    GetHostedPageForSubscriptionUpgrade:
      type: object
      properties:
        plan_id:
          type: string
          writeOnly: true
        subscription_id:
          type: string
          writeOnly: true
        url:
          type: string
          format: uri
          readOnly: true
      required:
      - plan_id
      - subscription_id
    GitLabConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        gitlab_instance_url:
          type: string
          format: uri
          maxLength: 200
        access_token:
          type: string
          maxLength: 300
        labeling_enabled:
          type: boolean
      required:
      - access_token
      - gitlab_instance_url
    GithubConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        installation_id:
          type: string
          maxLength: 100
        organisation:
          type: integer
          readOnly: true
      required:
      - installation_id
    GithubLogin:
      type: object
      properties:
        access_token:
          type: string
          description: Code or access token returned from the FE interaction with
            the third party login provider.
        sign_up_type:
          writeOnly: true
          description: |-
            Provide information about how the user signed up (i.e. via invite or not)

            * `NO_INVITE` - No Invite
            * `INVITE_EMAIL` - Invite Email
            * `INVITE_LINK` - Invite Link
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        hubspot_cookie:
          type:
          - string
          - 'null'
        marketing_consent_given:
          type:
          - boolean
          - 'null'
        utm_data:
          oneOf:
          - $ref: '#/components/schemas/UTMData'
          - type: 'null'
      required:
      - access_token
    GithubRepository:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        github_configuration:
          type: integer
          readOnly: true
        project:
          type: integer
        repository_owner:
          type: string
          maxLength: 100
        repository_name:
          type: string
          maxLength: 100
        tagging_enabled:
          type: boolean
      required:
      - project
      - repository_name
      - repository_owner
    GoogleLogin:
      type: object
      properties:
        access_token:
          type: string
          description: Code or access token returned from the FE interaction with
            the third party login provider.
        sign_up_type:
          writeOnly: true
          description: |-
            Provide information about how the user signed up (i.e. via invite or not)

            * `NO_INVITE` - No Invite
            * `INVITE_EMAIL` - Invite Email
            * `INVITE_LINK` - Invite Link
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        hubspot_cookie:
          type:
          - string
          - 'null'
        marketing_consent_given:
          type:
          - boolean
          - 'null'
        utm_data:
          oneOf:
          - $ref: '#/components/schemas/UTMData'
          - type: 'null'
      required:
      - access_token
    GrafanaOrganisationConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
      required:
      - api_key
    GrafanaProjectConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
      required:
      - api_key
    Group:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
      required:
      - id
      - name
    HeapConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
      required:
      - api_key
    IdentifierOnlyIdentity:
      type: object
      properties:
        identifier:
          type: string
          maxLength: 2000
      required:
      - identifier
    Identity:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        identifier:
          type: string
          maxLength: 2000
        environment:
          type: integer
          readOnly: true
      required:
      - identifier
    IdentityAllFeatureStates:
      type: object
      properties:
        feature:
          $ref: '#/components/schemas/IdentityAllFeatureStatesFeature'
        enabled:
          type: boolean
        feature_state_value:
          oneOf:
          - type: string
          - type: integer
          - type: boolean
          readOnly: true
          description: 'Can be any of the following types: integer, boolean, string.'
        overridden_by:
          type:
          - string
          - 'null'
          readOnly: true
          description: 'One of: null, ''SEGMENT'', ''IDENTITY''.'
        segment:
          allOf:
          - $ref: '#/components/schemas/IdentityAllFeatureStatesSegment'
          readOnly: true
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/IdentityAllFeatureStatesMVFeatureStateValue'
      required:
      - enabled
      - feature
      - multivariate_feature_state_values
    IdentityAllFeatureStatesFeature:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        type:
          type: string
      required:
      - id
      - name
      - type
    IdentityAllFeatureStatesMVFeatureOption:
      type: object
      properties:
        value:
          oneOf:
          - type: string
          - type: integer
          - type: boolean
          description: 'Can be any of the following types: integer, boolean, string.'
          readOnly: true
    IdentityAllFeatureStatesMVFeatureStateValue:
      type: object
      properties:
        multivariate_feature_option:
          $ref: '#/components/schemas/IdentityAllFeatureStatesMVFeatureOption'
        percentage_allocation:
          type: number
          format: double
      required:
      - multivariate_feature_option
      - percentage_allocation
    IdentityAllFeatureStatesSegment:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
      required:
      - id
      - name
    IdentitySourceIdentityRequest:
      type: object
      properties:
        source_identity_id:
          type: integer
          description: ID of the source identity to clone feature states from.
      required:
      - source_identity_id
    IncrementTraitValue:
      type: object
      properties:
        trait_key:
          type: string
        increment_by:
          type: integer
          writeOnly: true
        identifier:
          type: string
        trait_value:
          type: integer
          readOnly: true
      required:
      - identifier
      - increment_by
      - trait_key
    InfluxData:
      type: object
      properties:
        events_list:
          type: array
          items:
            type: object
            additionalProperties: {}
      required:
      - events_list
    Invite:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          maxLength: 254
        role:
          $ref: '#/components/schemas/RoleEnum'
        date_created:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        permission_groups:
          type: array
          items:
            type:
            - integer
            - 'null'
      required:
      - email
    InviteLink:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        hash:
          type: string
          readOnly: true
        date_created:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        role:
          $ref: '#/components/schemas/RoleEnum'
        expires_at:
          type:
          - string
          - 'null'
          format: date-time
          description: Datetime that the invite link will cease to be active. Leave
            blank to enable indefinitely.
    InviteList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          maxLength: 254
        date_created:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        invited_by:
          $ref: '#/components/schemas/UserList'
        permission_groups:
          type: array
          items:
            type: integer
      required:
      - email
      - invited_by
    Labels:
      type: object
      properties:
        client_application_name:
          type:
          - string
          - 'null'
        client_application_version:
          type:
          - string
          - 'null'
        user_agent:
          type:
          - string
          - 'null'
    LaunchDarklyImportRequest:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        created_by:
          type: string
          format: email
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        completed_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        status:
          $ref: '#/components/schemas/LaunchDarklyImportRequestStatus'
        project:
          type: integer
          readOnly: true
      required:
      - status
    LaunchDarklyImportRequestStatus:
      type: object
      properties:
        requested_environment_count:
          type: integer
          readOnly: true
        requested_flag_count:
          type: integer
          readOnly: true
        deprecated_flag_count:
          type: integer
          readOnly: true
          default: 0
        result:
          readOnly: true
          oneOf:
          - $ref: '#/components/schemas/ResultEnum'
          - $ref: '#/components/schemas/NullEnum'
        error_messages:
          type: array
          items:
            type: string
            readOnly: true
      required:
      - error_messages
    ListFeature:
      type: object
      description: Functionality for serializers that need to handle metadata
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 2000
        type:
          oneOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          - $ref: '#/components/schemas/BlankEnum'
        default_enabled:
          type: boolean
        initial_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        description:
          type:
          - string
          - 'null'
        tags:
          type: array
          items:
            type: integer
        multivariate_options:
          type: array
          items:
            $ref: '#/components/schemas/NestedMultivariateFeatureOption'
        is_archived:
          type: boolean
        owners:
          type: array
          items:
            type: integer
        group_owners:
          type: array
          items:
            type: integer
        uuid:
          type: string
          format: uuid
          readOnly: true
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        environment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        segment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        num_segment_overrides:
          type: integer
          readOnly: true
          description: Number of segment overrides that exist for the given feature
            in the environment provided by the `environment` query parameter.
        num_identity_overrides:
          type:
          - integer
          - 'null'
          readOnly: true
          description: 'Number of identity overrides that exist for the given feature
            in the environment provided by the `environment` query parameter. Note:
            will return null for Edge enabled projects.'
        is_num_identity_overrides_complete:
          type: boolean
          readOnly: true
          default: true
        is_server_key_only:
          type: boolean
        last_modified_in_any_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the given project. Note: requires feature versioning
            v2 enabled on the environment.'
        last_modified_in_current_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the current environment. Note: requires that the
            environment query parameter is passed and feature versioning v2 enabled
            on the environment.'
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
        code_references_counts:
          type: array
          items:
            $ref: '#/components/schemas/FeatureFlagCodeReferencesRepositoryCount'
          readOnly: true
      required:
      - name
    ListUserEnvironmentPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        user:
          $ref: '#/components/schemas/UserList'
      required:
      - user
    ListUserPermissionGroup:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 200
        users:
          type: array
          items:
            $ref: '#/components/schemas/ListUserPermissionGroupMembership'
          readOnly: true
        is_default:
          type: boolean
          description: If set to true, all new users will be added to this group
        external_id:
          type:
          - string
          - 'null'
          description: Unique ID of the group in an external system
          maxLength: 255
      required:
      - name
    ListUserPermissionGroupEnvironmentPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        group:
          $ref: '#/components/schemas/UserPermissionGroupSerializerDetail'
      required:
      - group
    ListUserPermissionGroupMembership:
      type: object
      properties:
        id:
          type: integer
        email:
          type: string
          format: email
        first_name:
          type: string
        last_name:
          type: string
        last_login:
          type: string
        group_admin:
          type: boolean
      required:
      - email
      - first_name
      - id
      - last_login
      - last_name
    ListUserPermissionGroupProjectPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        group:
          $ref: '#/components/schemas/UserPermissionGroup'
      required:
      - group
    ListUserProjectPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        user:
          $ref: '#/components/schemas/UserList'
      required:
      - user
    MasterAPIKey:
      type: object
      properties:
        id:
          type: string
          readOnly: true
        prefix:
          type: string
          readOnly: true
        created:
          type: string
          format: date-time
          readOnly: true
        name:
          type: string
          description: A free-form name for the API key. Need not be unique. 50 characters
            max.
          maxLength: 50
        revoked:
          type: boolean
          description: If the API key is revoked, clients cannot use it anymore. (This
            cannot be undone.)
        expiry_date:
          type:
          - string
          - 'null'
          format: date-time
          title: Expires
          description: Once API key expires, clients cannot use it anymore.
        key:
          type: string
          readOnly: true
          description: 'Since we don''t store the api key itself(i.e: we only store
            the hash) this key will be none for every endpoint apart from create'
        is_admin:
          type: boolean
          default: true
        has_expired:
          type: boolean
          readOnly: true
        created_by:
          type:
          - integer
          - 'null'
          readOnly: true
    MetaDataModelField:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        field:
          type: integer
        content_type:
          type: integer
        is_required_for:
          type: array
          items:
            $ref: '#/components/schemas/MetadataModelFieldRequirement'
      required:
      - content_type
      - field
    Metadata:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        model_field:
          type: integer
        field_value:
          type: string
          maxLength: 2000
      required:
      - field_value
      - model_field
    MetadataField:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 255
        type:
          $ref: '#/components/schemas/MetadataFieldTypeEnum'
        description:
          type:
          - string
          - 'null'
        organisation:
          type: integer
        project:
          type:
          - integer
          - 'null'
        model_fields:
          type: array
          items:
            $ref: '#/components/schemas/MetadataModelFieldNested'
          readOnly: true
      required:
      - name
      - organisation
    MetadataFieldTypeEnum:
      enum:
      - int
      - str
      - bool
      - url
      - multiline_str
      type: string
      description: |-
        * `int` - Integer
        * `str` - String
        * `bool` - Boolean
        * `url` - Url
        * `multiline_str` - Multiline String
    MetadataModelFieldNested:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        content_type:
          type: integer
        is_required_for:
          type: array
          items:
            $ref: '#/components/schemas/MetadataModelFieldRequirement'
          readOnly: true
      required:
      - content_type
    MetadataModelFieldRequirement:
      type: object
      properties:
        content_type:
          type: integer
        object_id:
          type: integer
          maximum: 2147483647
          minimum: 0
      required:
      - content_type
      - object_id
    MetricItem:
      type: object
      properties:
        value:
          type: integer
        description:
          type: string
        name:
          type: string
        entity:
          type: string
        rank:
          type: integer
      required:
      - description
      - entity
      - name
      - value
    MixpanelConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
      required:
      - api_key
    Monitoring:
      type: object
      properties:
        waiting:
          type: integer
          readOnly: true
    MultiInvites:
      type: object
      properties:
        invites:
          type: array
          items:
            $ref: '#/components/schemas/Invite'
        emails:
          type: array
          items:
            type: string
            format: email
    MultivariateFeatureOption:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        type:
          oneOf:
          - $ref: '#/components/schemas/Type975Enum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        integer_value:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        string_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        boolean_value:
          type:
          - boolean
          - 'null'
        default_percentage_allocation:
          type: number
          format: double
          maximum: 100
          minimum: 0
        feature:
          type: integer
      required:
      - feature
    MultivariateFeatureStateValue:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        multivariate_feature_option:
          type: integer
        percentage_allocation:
          type: number
          format: double
          maximum: 100
          minimum: 0
      required:
      - multivariate_feature_option
      - percentage_allocation
    MultivariateOptionValues:
      type: object
      properties:
        value:
          oneOf:
          - type: string
          - type: integer
          - type: boolean
          - type: 'null'
          description: |-
            Given the *incoming* primitive data, return the value for this field
            that should be validated and transformed to a native value.
          readOnly: true
    NameEnum:
      enum:
      - Webhook
      - Grafana
      type: string
      description: |-
        * `Webhook` - Webhook
        * `Grafana` - Grafana
    NestedMultivariateFeatureOption:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        type:
          oneOf:
          - $ref: '#/components/schemas/Type975Enum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        integer_value:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        string_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        boolean_value:
          type:
          - boolean
          - 'null'
        default_percentage_allocation:
          type: number
          format: double
          maximum: 100
          minimum: 0
    NewRelicConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
        app_id:
          type: string
          maxLength: 100
      required:
      - api_key
      - app_id
    NullEnum:
      type: 'null'
    OrganisationAPIUsageNotification:
      type: object
      properties:
        organisation_id:
          type: integer
        percent_usage:
          type: integer
        notified_at:
          type: string
          format: date-time
      required:
      - notified_at
      - organisation_id
      - percent_usage
    OrganisationSerializerBasic:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 2000
      required:
      - name
    OrganisationSerializerFull:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        webhook_notification_email:
          type:
          - string
          - 'null'
          format: email
          maxLength: 254
        num_seats:
          type: integer
          readOnly: true
        subscription:
          $ref: '#/components/schemas/Subscription'
        role:
          type:
          - string
          - 'null'
          readOnly: true
        persist_trait_data:
          type: boolean
          readOnly: true
          description: Disable this if you don't want Flagsmith to store trait data
            for this org's identities.
        block_access_to_admin:
          type: boolean
          readOnly: true
          description: Enable this to block all the access to admin interface for
            the organisation
        restrict_project_create_to_admin:
          type: boolean
        force_2fa:
          type: boolean
      required:
      - name
    OrganisationWebhook:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          maxLength: 200
        enabled:
          type: boolean
        secret:
          type: string
          maxLength: 255
        created_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        updated_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
      required:
      - url
    PaginatedAuditLogListList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/AuditLogList'
    PaginatedContentTypeList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/ContentType'
    PaginatedEdgeIdentityList:
      type: object
      required:
      - results
      properties:
        last_evaluated_key:
          type: string
          nullable: true
        results:
          type: array
          items:
            $ref: '#/components/schemas/EdgeIdentity'
    PaginatedEdgeIdentityTraitsList:
      type: object
      required:
      - results
      properties:
        last_evaluated_key:
          type: string
          nullable: true
        results:
          type: array
          items:
            $ref: '#/components/schemas/EdgeIdentityTraits'
    PaginatedEnvironmentFeatureVersionList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/EnvironmentFeatureVersion'
    PaginatedEnvironmentMetricsList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/EnvironmentMetrics'
    PaginatedEnvironmentSerializerWithMetadataList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/EnvironmentSerializerWithMetadata'
    PaginatedFeatureExportList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/FeatureExport'
    PaginatedFeatureExternalResourceList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/FeatureExternalResource'
    PaginatedFeatureImportList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/FeatureImport'
    PaginatedFeatureSegmentListList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/FeatureSegmentList'
    PaginatedFeatureStateSerializerWithIdentityList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/FeatureStateSerializerWithIdentity'
    PaginatedGithubConfigurationList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/GithubConfiguration'
    PaginatedGithubRepositoryList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/GithubRepository'
    PaginatedIdentityAllFeatureStatesList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/IdentityAllFeatureStates'
    PaginatedIdentityList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/Identity'
    PaginatedInviteListList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/InviteList'
    PaginatedListFeatureList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/ListFeature'
    PaginatedListUserPermissionGroupList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/ListUserPermissionGroup'
    PaginatedMasterAPIKeyList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/MasterAPIKey'
    PaginatedMetaDataModelFieldList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/MetaDataModelField'
    PaginatedMetadataFieldList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/MetadataField'
    PaginatedMultivariateFeatureOptionList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureOption'
    PaginatedOrganisationAPIUsageNotificationList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/OrganisationAPIUsageNotification'
    PaginatedOrganisationSerializerFullList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/OrganisationSerializerFull'
    PaginatedOrganisationWebhookList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/OrganisationWebhook'
    PaginatedPaginatedQueryParamsList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/PaginatedQueryParams'
    PaginatedPermissionModelList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/PermissionModel'
    PaginatedQueryParams:
      type: object
      properties:
        page:
          type: integer
          minimum: 1
          default: 1
        page_size:
          type: integer
          maximum: 100
          minimum: 1
          default: 100
    PaginatedSearchQueryParamsList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/SearchQueryParams'
    PaginatedSegmentList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/Segment'
    PaginatedTagList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/Tag'
    PaginatedTraitList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/Trait'
    PaginatedUserList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/User'
    PaginatedWritableNestedFeatureStateList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/WritableNestedFeatureState'
    PasswordResetConfirmRetype:
      type: object
      properties:
        uid:
          type: string
        token:
          type: string
        new_password:
          type: string
        re_new_password:
          type: string
      required:
      - new_password
      - re_new_password
      - token
      - uid
    PatchedAmplitudeConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
        base_url:
          type: string
          format: uri
          maxLength: 200
    PatchedCreateUpdateUserEnvironmentPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        user:
          type: integer
    PatchedCreateUpdateUserPermissionGroupEnvironmentPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        group:
          type: integer
    PatchedCreateUpdateUserPermissionGroupProjectPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        group:
          type: integer
    PatchedCreateUpdateUserProjectPermission:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        user:
          type: integer
    PatchedCustomCurrentUser:
      type: object
      properties:
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        sign_up_type:
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          readOnly: true
        auth_type:
          type: string
          readOnly: true
        is_superuser:
          type: boolean
          readOnly: true
        date_joined:
          type: string
          format: date-time
        uuid:
          type: string
          format: uuid
          readOnly: true
        pylon_email_signature:
          type: string
          readOnly: true
    PatchedCustomEnvironmentFeatureVersionFeatureState:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature:
          type: integer
          readOnly: true
        enabled:
          type: boolean
        feature_state_value:
          $ref: '#/components/schemas/FeatureStateValue'
        feature_segment:
          oneOf:
          - $ref: '#/components/schemas/CustomCreateSegmentOverrideFeatureSegment'
          - type: 'null'
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        environment:
          type:
          - integer
          - 'null'
          readOnly: true
        identity:
          type:
          - integer
          - 'null'
          readOnly: true
        change_request:
          type:
          - integer
          - 'null'
          readOnly: true
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
    PatchedDataDogConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type: string
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
        use_custom_source:
          type: boolean
    PatchedDynatraceConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
        entity_selector:
          type: string
          maxLength: 1000
    PatchedEdgeIdentityUpdate:
      type: object
      properties:
        identity_uuid:
          type: string
          readOnly: true
        identifier:
          type: string
          readOnly: true
          maxLength: 2000
        dashboard_alias:
          type: string
          maxLength: 100
    PatchedEnvironmentAPIKey:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        key:
          type: string
          readOnly: true
        active:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        name:
          type: string
          maxLength: 100
        expires_at:
          type:
          - string
          - 'null'
          format: date-time
    PatchedFeatureExternalResource:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          format: uri
          maxLength: 200
        type:
          $ref: '#/components/schemas/FeatureExternalResourceTypeEnum'
        metadata:
          oneOf:
          - {}
          - type: 'null'
        feature:
          type: integer
    PatchedFeatureSegmentCreate:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        feature:
          type: integer
        segment:
          type: integer
        environment:
          type: integer
        priority:
          type: integer
          readOnly: true
    PatchedFeatureStateSerializerCreate:
      type: object
      properties:
        feature:
          type: integer
        enabled:
          type: boolean
    PatchedGitLabConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        gitlab_instance_url:
          type: string
          format: uri
          maxLength: 200
        access_token:
          type: string
          maxLength: 300
        labeling_enabled:
          type: boolean
    PatchedGithubConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        installation_id:
          type: string
          maxLength: 100
        organisation:
          type: integer
          readOnly: true
    PatchedGithubRepository:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        github_configuration:
          type: integer
          readOnly: true
        project:
          type: integer
        repository_owner:
          type: string
          maxLength: 100
        repository_name:
          type: string
          maxLength: 100
        tagging_enabled:
          type: boolean
    PatchedGrafanaOrganisationConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
    PatchedGrafanaProjectConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
    PatchedHeapConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
    PatchedIdentity:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        identifier:
          type: string
          maxLength: 2000
        environment:
          type: integer
          readOnly: true
    PatchedListUserPermissionGroup:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 200
        users:
          type: array
          items:
            $ref: '#/components/schemas/ListUserPermissionGroupMembership'
          readOnly: true
        is_default:
          type: boolean
          description: If set to true, all new users will be added to this group
        external_id:
          type:
          - string
          - 'null'
          description: Unique ID of the group in an external system
          maxLength: 255
    PatchedMasterAPIKey:
      type: object
      properties:
        id:
          type: string
          readOnly: true
        prefix:
          type: string
          readOnly: true
        created:
          type: string
          format: date-time
          readOnly: true
        name:
          type: string
          description: A free-form name for the API key. Need not be unique. 50 characters
            max.
          maxLength: 50
        revoked:
          type: boolean
          description: If the API key is revoked, clients cannot use it anymore. (This
            cannot be undone.)
        expiry_date:
          type:
          - string
          - 'null'
          format: date-time
          title: Expires
          description: Once API key expires, clients cannot use it anymore.
        key:
          type: string
          readOnly: true
          description: 'Since we don''t store the api key itself(i.e: we only store
            the hash) this key will be none for every endpoint apart from create'
        is_admin:
          type: boolean
          default: true
        has_expired:
          type: boolean
          readOnly: true
        created_by:
          type:
          - integer
          - 'null'
          readOnly: true
    PatchedMetaDataModelField:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        field:
          type: integer
        content_type:
          type: integer
        is_required_for:
          type: array
          items:
            $ref: '#/components/schemas/MetadataModelFieldRequirement'
    PatchedMetadataField:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 255
        type:
          $ref: '#/components/schemas/MetadataFieldTypeEnum'
        description:
          type:
          - string
          - 'null'
        organisation:
          type: integer
        project:
          type:
          - integer
          - 'null'
        model_fields:
          type: array
          items:
            $ref: '#/components/schemas/MetadataModelFieldNested'
          readOnly: true
    PatchedMixpanelConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
    PatchedMultivariateFeatureOption:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        type:
          oneOf:
          - $ref: '#/components/schemas/Type975Enum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        integer_value:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        string_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        boolean_value:
          type:
          - boolean
          - 'null'
        default_percentage_allocation:
          type: number
          format: double
          maximum: 100
          minimum: 0
        feature:
          type: integer
    PatchedNewRelicConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
        app_id:
          type: string
          maxLength: 100
    PatchedOrganisationSerializerFull:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        webhook_notification_email:
          type:
          - string
          - 'null'
          format: email
          maxLength: 254
        num_seats:
          type: integer
          readOnly: true
        subscription:
          $ref: '#/components/schemas/Subscription'
        role:
          type:
          - string
          - 'null'
          readOnly: true
        persist_trait_data:
          type: boolean
          readOnly: true
          description: Disable this if you don't want Flagsmith to store trait data
            for this org's identities.
        block_access_to_admin:
          type: boolean
          readOnly: true
          description: Enable this to block all the access to admin interface for
            the organisation
        restrict_project_create_to_admin:
          type: boolean
        force_2fa:
          type: boolean
    PatchedOrganisationWebhook:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          maxLength: 200
        enabled:
          type: boolean
        secret:
          type: string
          maxLength: 255
        created_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        updated_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
    PatchedProjectUpdate:
      type: object
      description: |-
        Mixin to add read only status to fields in a given serializer based on the existence
        of a subscription and a black list of plan ids

        Example usage:

            class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
                class Meta:
                    model = MyModel
                    fields = ("my_field",)

                invalid_plans = ("free",)
                field_names = ("my_field",)

                def get_subscription(self):
                    return subscription
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        organisation:
          type: integer
          readOnly: true
        hide_disabled_flags:
          type: boolean
          description: If true will exclude flags from SDK which are disabled
        enable_dynamo_db:
          type: boolean
          readOnly: true
          description: If true will sync environment data with dynamodb and allow
            access to dynamodb identities
        migration_status:
          type: string
          readOnly: true
          description: 'Edge migration status of the project; can be one of: MIGRATION_SCHEDULED,
            MIGRATION_COMPLETED, MIGRATION_IN_PROGRESS, MIGRATION_NOT_STARTED, NOT_APPLICABLE'
        use_edge_identities:
          type: boolean
          readOnly: true
        prevent_flag_defaults:
          type: boolean
          description: Prevent defaults from being set in all environments when creating
            a feature.
        enable_realtime_updates:
          type: boolean
          readOnly: true
          description: Enable this to trigger a realtime(sse) event whenever the value
            of a flag changes
        only_allow_lower_case_feature_names:
          type: boolean
          description: Used by UI to validate feature names
        feature_name_regex:
          type:
          - string
          - 'null'
          description: Used for validating feature names
          maxLength: 255
        show_edge_identity_overrides_for_feature:
          type: boolean
          readOnly: true
        stale_flags_limit_days:
          type: integer
          maximum: 2147483647
          minimum: -2147483648
          readOnly: true
          description: Number of days without modification in any environment before
            a flag is considered stale.
        edge_v2_migration_status:
          allOf:
          - $ref: '#/components/schemas/EdgeV2MigrationStatusEnum'
          readOnly: true
          description: |-
            [Edge V2 migration] Project migration status. Set to `IN_PROGRESS` to trigger migration start.

            * `NOT_STARTED` - Not Started
            * `IN_PROGRESS` - In Progress
            * `COMPLETE` - Complete
            * `INCOMPLETE` - Incomplete (identity overrides skipped)
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        enforce_feature_owners:
          type: boolean
          description: Require at least one user or group owner when creating a feature.
    PatchedRudderstackConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
    PatchedSegment:
      type: object
      description: Functionality for serializers that need to handle metadata
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        created_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        updated_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        name:
          type: string
          maxLength: 2000
        description:
          type:
          - string
          - 'null'
        project:
          type: integer
        feature:
          type:
          - integer
          - 'null'
        version_of:
          type:
          - integer
          - 'null'
        rules:
          type: array
          items:
            $ref: '#/components/schemas/SegmentRule'
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
        membership_counts:
          type: array
          items:
            $ref: '#/components/schemas/SegmentMembershipCount'
          readOnly: true
    PatchedSegmentConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
        base_url:
          allOf:
          - $ref: '#/components/schemas/BaseUrlEnum'
          default: https://api.segment.io/
    PatchedSentryChangeTrackingConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        environment:
          type: integer
          readOnly: true
        webhook_url:
          type: string
          format: uri
          maxLength: 200
        secret:
          type: string
          maxLength: 60
          minLength: 10
    PatchedSlackEnvironment:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        channel_id:
          type: string
          description: Id of the slack channel to post messages to
          maxLength: 50
        enabled:
          type: boolean
    PatchedTag:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        label:
          type: string
          maxLength: 100
        color:
          type: string
          description: Hexadecimal value of the tag color
          maxLength: 10
        description:
          type:
          - string
          - 'null'
          maxLength: 512
        project:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        is_permanent:
          type: boolean
          description: When applied to a feature, it means this feature should be
            excluded from stale flags logic.
        is_system_tag:
          type: boolean
          readOnly: true
          description: Indicates that a tag was created by the system, not the user.
        type:
          allOf:
          - $ref: '#/components/schemas/TagTypeEnum'
          readOnly: true
          description: |-
            Field used to provide a consistent identifier for the FE and API to use for business logic.

            * `NONE` - None
            * `STALE` - Stale
            * `GITHUB` - Github
            * `UNHEALTHY` - Unhealthy
            * `GITLAB` - Gitlab
    PatchedTrait:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        trait_key:
          type: string
          maxLength: 200
        value_type:
          oneOf:
          - $ref: '#/components/schemas/ValueTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        integer_value:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        string_value:
          type:
          - string
          - 'null'
          maxLength: 2000
        boolean_value:
          type:
          - boolean
          - 'null'
        float_value:
          type:
          - number
          - 'null'
          format: double
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
    PatchedUpdateEnvironment:
      type: object
      description: |-
        Mixin to add read only status to fields in a given serializer based on the existence
        of a subscription and a black list of plan ids

        Example usage:

            class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
                class Meta:
                    model = MyModel
                    fields = ("my_field",)

                invalid_plans = ("free",)
                field_names = ("my_field",)

                def get_subscription(self):
                    return subscription
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          maxLength: 100
        description:
          type:
          - string
          - 'null'
          maxLength: 20000
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
          readOnly: true
        allow_client_traits:
          type: boolean
          description: Allows clients using the client API key to set traits.
        banner_text:
          type:
          - string
          - 'null'
          maxLength: 255
        banner_colour:
          type:
          - string
          - 'null'
          description: hex code for the banner colour
          maxLength: 7
        hide_disabled_flags:
          type:
          - boolean
          - 'null'
          description: 'If true will exclude flags from SDK which are disabled. NOTE:
            If set, this will override the project `hide_disabled_flags`'
        use_mv_v2_evaluation:
          type: boolean
          description: |-
            To avoid breaking the API, we return this field as well.

            Warning: this will still mean that sending the `use_mv_v2_evaluation` field
            (e.g. in a PUT request) will not behave as expected but, since this is a minor
            issue, I think we can ignore.
          readOnly: true
        use_identity_composite_key_for_hashing:
          type: boolean
          description: Enable this to have consistent multivariate and percentage
            split evaluations across all SDKs (in local and server side mode)
        hide_sensitive_data:
          type: boolean
          description: 'If true, will hide sensitive data(e.g: traits, description
            etc) from the SDK endpoints'
        use_v2_feature_versioning:
          type: boolean
          readOnly: true
        use_identity_overrides_in_local_eval:
          type: boolean
          description: When enabled, identity overrides will be included in the environment
            document
        is_creating:
          type: boolean
          readOnly: true
          description: Attribute used to indicate when an environment is still being
            created (via clone for example)
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
    PatchedUpdateFeature:
      type: object
      description: prevent users from changing certain values after creation
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          readOnly: true
        type:
          oneOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          - $ref: '#/components/schemas/BlankEnum'
        default_enabled:
          type: boolean
          readOnly: true
        initial_value:
          type:
          - string
          - 'null'
          readOnly: true
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        description:
          type:
          - string
          - 'null'
        tags:
          type: array
          items:
            type: integer
        multivariate_options:
          type: array
          items:
            $ref: '#/components/schemas/NestedMultivariateFeatureOption'
        is_archived:
          type: boolean
        owners:
          type: array
          items:
            type: integer
          readOnly: true
        group_owners:
          type: array
          items:
            type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        environment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        segment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        num_segment_overrides:
          type: integer
          readOnly: true
          description: Number of segment overrides that exist for the given feature
            in the environment provided by the `environment` query parameter.
        num_identity_overrides:
          type:
          - integer
          - 'null'
          readOnly: true
          description: 'Number of identity overrides that exist for the given feature
            in the environment provided by the `environment` query parameter. Note:
            will return null for Edge enabled projects.'
        is_num_identity_overrides_complete:
          type: boolean
          readOnly: true
          default: true
        is_server_key_only:
          type: boolean
        last_modified_in_any_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the given project. Note: requires feature versioning
            v2 enabled on the environment.'
        last_modified_in_current_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the current environment. Note: requires that the
            environment query parameter is passed and feature versioning v2 enabled
            on the environment.'
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
        code_references_counts:
          type: array
          items:
            $ref: '#/components/schemas/FeatureFlagCodeReferencesRepositoryCount'
          readOnly: true
    PatchedUser:
      type: object
      properties:
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        sign_up_type:
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          readOnly: true
    PatchedUserOrganisationPermissionUpdateCreate:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        user:
          type: integer
        permissions:
          type: array
          items:
            type: string
    PatchedUserPermissionGroupOrganisationPermissionUpdateCreate:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        group:
          type: integer
        permissions:
          type: array
          items:
            type: string
    PatchedWarehouseConnection:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        warehouse_type:
          $ref: '#/components/schemas/WarehouseTypeEnum'
        status:
          allOf:
          - $ref: '#/components/schemas/WarehouseConnectionStatusEnum'
          readOnly: true
        name:
          type: string
          maxLength: 255
        config:
          oneOf:
          - {}
          - type: 'null'
        created_at:
          type: string
          format: date-time
          readOnly: true
    PatchedWebhook:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          maxLength: 200
        enabled:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        secret:
          type: string
          maxLength: 255
    PatchedWebhookConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          maxLength: 200
        secret:
          type: string
          maxLength: 255
    PatchedWritableNestedFeatureState:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature_state_value:
          $ref: '#/components/schemas/FeatureStateValue'
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
        identifier:
          type: string
          description: Can be passed as an alternative to `identity`
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        enabled:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        version:
          type:
          - integer
          - 'null'
          readOnly: true
        feature:
          type: integer
        environment:
          type:
          - integer
          - 'null'
        identity:
          type:
          - integer
          - 'null'
        feature_segment:
          type:
          - integer
          - 'null'
        change_request:
          type:
          - integer
          - 'null'
        environment_feature_version:
          type:
          - string
          - 'null'
          format: uuid
    PaymentMethodEnum:
      enum:
      - CHARGEBEE
      - XERO
      - AWS_MARKETPLACE
      type: string
      description: |-
        * `CHARGEBEE` - Chargebee
        * `XERO` - Xero
        * `AWS_MARKETPLACE` - AWS Marketplace
    PaymentSourceEnum:
      enum:
      - CHARGEBEE
      type: string
      description: '* `CHARGEBEE` - CHARGEBEE'
    PermissionModel:
      type: object
      properties:
        key:
          type: string
          maxLength: 100
        description:
          type: string
        supports_tag:
          type: boolean
          readOnly: true
      required:
      - description
      - key
    PermissionRole:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        tags:
          type: array
          items:
            type: integer
      required:
      - id
      - name
    PortalUrl:
      type: object
      properties:
        url:
          type: string
          format: uri
      required:
      - url
    ProjectCreate:
      type: object
      description: |-
        Mixin to add read only status to fields in a given serializer based on the existence
        of a subscription and a black list of plan ids

        Example usage:

            class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
                class Meta:
                    model = MyModel
                    fields = ("my_field",)

                invalid_plans = ("free",)
                field_names = ("my_field",)

                def get_subscription(self):
                    return subscription
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        organisation:
          type: integer
        hide_disabled_flags:
          type: boolean
          description: If true will exclude flags from SDK which are disabled
        enable_dynamo_db:
          type: boolean
          readOnly: true
          description: If true will sync environment data with dynamodb and allow
            access to dynamodb identities
        migration_status:
          type: string
          readOnly: true
          description: 'Edge migration status of the project; can be one of: MIGRATION_SCHEDULED,
            MIGRATION_COMPLETED, MIGRATION_IN_PROGRESS, MIGRATION_NOT_STARTED, NOT_APPLICABLE'
        use_edge_identities:
          type: boolean
          readOnly: true
        prevent_flag_defaults:
          type: boolean
          description: Prevent defaults from being set in all environments when creating
            a feature.
        enable_realtime_updates:
          type: boolean
          readOnly: true
          description: Enable this to trigger a realtime(sse) event whenever the value
            of a flag changes
        only_allow_lower_case_feature_names:
          type: boolean
          description: Used by UI to validate feature names
        feature_name_regex:
          type:
          - string
          - 'null'
          description: Used for validating feature names
          maxLength: 255
        show_edge_identity_overrides_for_feature:
          type: boolean
          readOnly: true
        stale_flags_limit_days:
          type: integer
          maximum: 2147483647
          minimum: -2147483648
          readOnly: true
          description: Number of days without modification in any environment before
            a flag is considered stale.
        edge_v2_migration_status:
          allOf:
          - $ref: '#/components/schemas/EdgeV2MigrationStatusEnum'
          readOnly: true
          description: |-
            [Edge V2 migration] Project migration status. Set to `IN_PROGRESS` to trigger migration start.

            * `NOT_STARTED` - Not Started
            * `IN_PROGRESS` - In Progress
            * `COMPLETE` - Complete
            * `INCOMPLETE` - Incomplete (identity overrides skipped)
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        enforce_feature_owners:
          type: boolean
          description: Require at least one user or group owner when creating a feature.
      required:
      - name
      - organisation
    ProjectFeature:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 2000
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        description:
          type:
          - string
          - 'null'
        initial_value:
          type:
          - string
          - 'null'
          maxLength: 20000
        default_enabled:
          type: boolean
        type:
          oneOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          - $ref: '#/components/schemas/BlankEnum'
        owners:
          type: array
          items:
            $ref: '#/components/schemas/UserList'
          readOnly: true
        group_owners:
          type: array
          items:
            $ref: '#/components/schemas/UserPermissionGroupSummary'
          readOnly: true
        is_server_key_only:
          type: boolean
      required:
      - name
    ProjectList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        organisation:
          type: integer
        hide_disabled_flags:
          type: boolean
          description: If true will exclude flags from SDK which are disabled
        enable_dynamo_db:
          type: boolean
          readOnly: true
          description: If true will sync environment data with dynamodb and allow
            access to dynamodb identities
        migration_status:
          type: string
          readOnly: true
          description: 'Edge migration status of the project; can be one of: MIGRATION_SCHEDULED,
            MIGRATION_COMPLETED, MIGRATION_IN_PROGRESS, MIGRATION_NOT_STARTED, NOT_APPLICABLE'
        use_edge_identities:
          type: boolean
          readOnly: true
        prevent_flag_defaults:
          type: boolean
          description: Prevent defaults from being set in all environments when creating
            a feature.
        enable_realtime_updates:
          type: boolean
          description: Enable this to trigger a realtime(sse) event whenever the value
            of a flag changes
        only_allow_lower_case_feature_names:
          type: boolean
          description: Used by UI to validate feature names
        feature_name_regex:
          type:
          - string
          - 'null'
          description: Used for validating feature names
          maxLength: 255
        show_edge_identity_overrides_for_feature:
          type: boolean
          readOnly: true
        stale_flags_limit_days:
          type: integer
          maximum: 2147483647
          minimum: -2147483648
          description: Number of days without modification in any environment before
            a flag is considered stale.
        edge_v2_migration_status:
          allOf:
          - $ref: '#/components/schemas/EdgeV2MigrationStatusEnum'
          readOnly: true
          description: |-
            [Edge V2 migration] Project migration status. Set to `IN_PROGRESS` to trigger migration start.

            * `NOT_STARTED` - Not Started
            * `IN_PROGRESS` - In Progress
            * `COMPLETE` - Complete
            * `INCOMPLETE` - Incomplete (identity overrides skipped)
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        enforce_feature_owners:
          type: boolean
          description: Require at least one user or group owner when creating a feature.
      required:
      - name
      - organisation
    ProjectRetrieve:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        organisation:
          type: integer
        hide_disabled_flags:
          type: boolean
          description: If true will exclude flags from SDK which are disabled
        enable_dynamo_db:
          type: boolean
          description: If true will sync environment data with dynamodb and allow
            access to dynamodb identities
        migration_status:
          type: string
          readOnly: true
          description: 'Edge migration status of the project; can be one of: MIGRATION_SCHEDULED,
            MIGRATION_COMPLETED, MIGRATION_IN_PROGRESS, MIGRATION_NOT_STARTED, NOT_APPLICABLE'
        use_edge_identities:
          type: boolean
          readOnly: true
        prevent_flag_defaults:
          type: boolean
          description: Prevent defaults from being set in all environments when creating
            a feature.
        enable_realtime_updates:
          type: boolean
          description: Enable this to trigger a realtime(sse) event whenever the value
            of a flag changes
        only_allow_lower_case_feature_names:
          type: boolean
          description: Used by UI to validate feature names
        feature_name_regex:
          type:
          - string
          - 'null'
          description: Used for validating feature names
          maxLength: 255
        show_edge_identity_overrides_for_feature:
          type: boolean
          readOnly: true
        stale_flags_limit_days:
          type: integer
          maximum: 2147483647
          minimum: -2147483648
          description: Number of days without modification in any environment before
            a flag is considered stale.
        edge_v2_migration_status:
          allOf:
          - $ref: '#/components/schemas/EdgeV2MigrationStatusEnum'
          description: |-
            [Edge V2 migration] Project migration status. Set to `IN_PROGRESS` to trigger migration start.

            * `NOT_STARTED` - Not Started
            * `IN_PROGRESS` - In Progress
            * `COMPLETE` - Complete
            * `INCOMPLETE` - Incomplete (identity overrides skipped)
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        enforce_feature_owners:
          type: boolean
          description: Require at least one user or group owner when creating a feature.
        max_segments_allowed:
          type: integer
          readOnly: true
          description: Max segments allowed for this project
        max_features_allowed:
          type: integer
          readOnly: true
          description: Max features allowed for this project
        max_segment_overrides_allowed:
          type: integer
          readOnly: true
          description: Max segments overrides allowed for any (one) environment within
            this project
        total_features:
          type: integer
          readOnly: true
        total_segments:
          type: integer
          readOnly: true
      required:
      - name
      - organisation
    ProjectUpdate:
      type: object
      description: |-
        Mixin to add read only status to fields in a given serializer based on the existence
        of a subscription and a black list of plan ids

        Example usage:

            class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
                class Meta:
                    model = MyModel
                    fields = ("my_field",)

                invalid_plans = ("free",)
                field_names = ("my_field",)

                def get_subscription(self):
                    return subscription
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        organisation:
          type: integer
          readOnly: true
        hide_disabled_flags:
          type: boolean
          description: If true will exclude flags from SDK which are disabled
        enable_dynamo_db:
          type: boolean
          readOnly: true
          description: If true will sync environment data with dynamodb and allow
            access to dynamodb identities
        migration_status:
          type: string
          readOnly: true
          description: 'Edge migration status of the project; can be one of: MIGRATION_SCHEDULED,
            MIGRATION_COMPLETED, MIGRATION_IN_PROGRESS, MIGRATION_NOT_STARTED, NOT_APPLICABLE'
        use_edge_identities:
          type: boolean
          readOnly: true
        prevent_flag_defaults:
          type: boolean
          description: Prevent defaults from being set in all environments when creating
            a feature.
        enable_realtime_updates:
          type: boolean
          readOnly: true
          description: Enable this to trigger a realtime(sse) event whenever the value
            of a flag changes
        only_allow_lower_case_feature_names:
          type: boolean
          description: Used by UI to validate feature names
        feature_name_regex:
          type:
          - string
          - 'null'
          description: Used for validating feature names
          maxLength: 255
        show_edge_identity_overrides_for_feature:
          type: boolean
          readOnly: true
        stale_flags_limit_days:
          type: integer
          maximum: 2147483647
          minimum: -2147483648
          readOnly: true
          description: Number of days without modification in any environment before
            a flag is considered stale.
        edge_v2_migration_status:
          allOf:
          - $ref: '#/components/schemas/EdgeV2MigrationStatusEnum'
          readOnly: true
          description: |-
            [Edge V2 migration] Project migration status. Set to `IN_PROGRESS` to trigger migration start.

            * `NOT_STARTED` - Not Started
            * `IN_PROGRESS` - In Progress
            * `COMPLETE` - Complete
            * `INCOMPLETE` - Incomplete (identity overrides skipped)
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        enforce_feature_owners:
          type: boolean
          description: Require at least one user or group owner when creating a feature.
      required:
      - name
    ResultEnum:
      enum:
      - success
      - failure
      - incomplete
      type: string
      description: |-
        * `success` - success
        * `failure` - failure
        * `incomplete` - incomplete
    RoleEnum:
      enum:
      - ADMIN
      - USER
      type: string
      description: |-
        * `ADMIN` - Admin
        * `USER` - User
    RudderstackConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        base_url:
          type:
          - string
          - 'null'
          format: uri
          maxLength: 200
        api_key:
          type: string
          maxLength: 100
      required:
      - api_key
    SDKAnalyticsFlags:
      type: object
      properties:
        evaluations:
          type: array
          items:
            $ref: '#/components/schemas/SDKAnalyticsFlagsSerializerDetail'
      required:
      - evaluations
    SDKAnalyticsFlagsSerializerDetail:
      type: object
      properties:
        feature_name:
          type: string
        identity_identifier:
          type: string
        enabled_when_evaluated:
          type: boolean
        count:
          type: integer
      required:
      - count
      - enabled_when_evaluated
      - feature_name
    SDKBulkCreateUpdateTrait:
      type: object
      properties:
        identity:
          $ref: '#/components/schemas/IdentifierOnlyIdentity'
        trait_value:
          type:
          - string
          - integer
          - number
          - boolean
          - 'null'
          description: Can be string, integer, float, or boolean
        trait_key:
          type: string
      required:
      - identity
      - trait_key
      - trait_value
    SDKCreateUpdateTrait:
      type: object
      properties:
        identity:
          $ref: '#/components/schemas/IdentifierOnlyIdentity'
        trait_value:
          type:
          - string
          - integer
          - number
          - boolean
          description: Can be string, integer, float, or boolean
        trait_key:
          type: string
      required:
      - identity
      - trait_key
      - trait_value
    Scope:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/WebhookScopeTypeEnum'
      required:
      - type
    SearchQueryParams:
      type: object
      properties:
        page:
          type: integer
          minimum: 1
          default: 1
        page_size:
          type: integer
          maximum: 100
          minimum: 1
          default: 100
        gitlab_project_id:
          type: integer
        search_text:
          type: string
        state:
          type: string
          default: opened
      required:
      - gitlab_project_id
    Segment:
      type: object
      description: Functionality for serializers that need to handle metadata
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        created_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        updated_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        name:
          type: string
          maxLength: 2000
        description:
          type:
          - string
          - 'null'
        project:
          type: integer
        feature:
          type:
          - integer
          - 'null'
        version_of:
          type:
          - integer
          - 'null'
        rules:
          type: array
          items:
            $ref: '#/components/schemas/SegmentRule'
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
        membership_counts:
          type: array
          items:
            $ref: '#/components/schemas/SegmentMembershipCount'
          readOnly: true
      required:
      - name
      - project
      - rules
    SegmentAssociatedFeatureState:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        feature:
          type: integer
        environment:
          type:
          - integer
          - 'null'
      required:
      - feature
    SegmentConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        api_key:
          type: string
          maxLength: 100
        base_url:
          allOf:
          - $ref: '#/components/schemas/BaseUrlEnum'
          default: https://api.segment.io/
      required:
      - api_key
    SegmentIdentifier:
      type: object
      properties:
        id:
          type: integer
      required:
      - id
    SegmentMembershipCount:
      type: object
      properties:
        environment:
          type: integer
          readOnly: true
        count:
          type: integer
          readOnly: true
        last_synced_at:
          type: string
          format: date-time
          readOnly: true
    SegmentOverride:
      type: object
      properties:
        segment_id:
          type: integer
        priority:
          type:
          - integer
          - 'null'
        enabled:
          type: boolean
        value:
          $ref: '#/components/schemas/FeatureValue'
      required:
      - enabled
      - segment_id
      - value
    SegmentRule:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        type:
          $ref: '#/components/schemas/SegmentRuleTypeEnum'
        rules:
          type: array
          items:
            $ref: '#/components/schemas/_NestedSegmentRule'
        conditions:
          type: array
          items:
            $ref: '#/components/schemas/Condition'
        delete:
          type: boolean
          writeOnly: true
      required:
      - type
    SegmentRuleTypeEnum:
      enum:
      - ALL
      - ANY
      - NONE
      type: string
      description: |-
        * `ALL` - all
        * `ANY` - any
        * `NONE` - none
    SelfHostedOnboardingSupportSendRequest:
      type: object
      properties:
        hubspotutk:
          type: string
    SendEmailReset:
      type: object
      properties:
        email:
          type: string
          format: email
      required:
      - email
    SentryChangeTrackingConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        environment:
          type: integer
          readOnly: true
        webhook_url:
          type: string
          format: uri
          maxLength: 200
        secret:
          type: string
          maxLength: 60
          minLength: 10
      required:
      - secret
      - webhook_url
    SetPasswordRetype:
      type: object
      properties:
        new_password:
          type: string
        re_new_password:
          type: string
        current_password:
          type: string
      required:
      - current_password
      - new_password
      - re_new_password
    SetUsername:
      type: object
      properties:
        current_password:
          type: string
        new_email:
          type: string
          format: email
          title: Email
          maxLength: 254
      required:
      - current_password
      - new_email
    SignUpTypeEnum:
      enum:
      - NO_INVITE
      - INVITE_EMAIL
      - INVITE_LINK
      type: string
      description: |-
        * `NO_INVITE` - No Invite
        * `INVITE_EMAIL` - Invite Email
        * `INVITE_LINK` - Invite Link
    SlackChannel:
      type: object
      properties:
        channel_name:
          type: string
        channel_id:
          type: string
      required:
      - channel_id
      - channel_name
    SlackChannelList:
      type: object
      properties:
        cursor:
          type: string
        channels:
          type: array
          items:
            $ref: '#/components/schemas/SlackChannel'
      required:
      - channels
      - cursor
    SlackEnvironment:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        channel_id:
          type: string
          description: Id of the slack channel to post messages to
          maxLength: 50
        enabled:
          type: boolean
      required:
      - channel_id
    Status6d4Enum:
      enum:
      - SUCCESS
      - PROCESSING
      - FAILED
      type: string
      description: |-
        * `SUCCESS` - Success
        * `PROCESSING` - Processing
        * `FAILED` - Failed
    Subscription:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        has_active_billing_periods:
          type: boolean
          readOnly: true
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        subscription_id:
          type:
          - string
          - 'null'
          maxLength: 100
        subscription_date:
          type:
          - string
          - 'null'
          format: date-time
        plan:
          type:
          - string
          - 'null'
          maxLength: 100
        max_seats:
          type: integer
          maximum: 2147483647
          minimum: -2147483648
        max_api_calls:
          type: integer
          maximum: 9223372036854775807
          minimum: -9223372036854775808
          format: int64
        cancellation_date:
          type:
          - string
          - 'null'
          format: date-time
        customer_id:
          type:
          - string
          - 'null'
          maxLength: 100
        billing_status:
          oneOf:
          - $ref: '#/components/schemas/BillingStatusEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        payment_method:
          oneOf:
          - $ref: '#/components/schemas/PaymentMethodEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        notes:
          type:
          - string
          - 'null'
          maxLength: 500
    SubscriptionDetails:
      type: object
      properties:
        max_seats:
          type: integer
        max_api_calls:
          type: integer
        max_projects:
          type:
          - integer
          - 'null'
        payment_source:
          oneOf:
          - $ref: '#/components/schemas/PaymentSourceEnum'
          - $ref: '#/components/schemas/NullEnum'
        chargebee_email:
          type: string
          format: email
        feature_history_visibility_days:
          type:
          - integer
          - 'null'
        audit_log_visibility_days:
          type:
          - integer
          - 'null'
      required:
      - audit_log_visibility_days
      - chargebee_email
      - feature_history_visibility_days
      - max_api_calls
      - max_projects
      - max_seats
      - payment_source
    Tag:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        label:
          type: string
          maxLength: 100
        color:
          type: string
          description: Hexadecimal value of the tag color
          maxLength: 10
        description:
          type:
          - string
          - 'null'
          maxLength: 512
        project:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        is_permanent:
          type: boolean
          description: When applied to a feature, it means this feature should be
            excluded from stale flags logic.
        is_system_tag:
          type: boolean
          readOnly: true
          description: Indicates that a tag was created by the system, not the user.
        type:
          allOf:
          - $ref: '#/components/schemas/TagTypeEnum'
          readOnly: true
          description: |-
            Field used to provide a consistent identifier for the FE and API to use for business logic.

            * `NONE` - None
            * `STALE` - Stale
            * `GITHUB` - Github
            * `UNHEALTHY` - Unhealthy
            * `GITLAB` - Gitlab
      required:
      - label
    TagBasedPermission:
      type: object
      properties:
        permissions:
          type: array
          items:
            type: string
        tags:
          type: array
          items:
            type: integer
      required:
      - permissions
      - tags
    TagTypeEnum:
      enum:
      - NONE
      - STALE
      - GITHUB
      - UNHEALTHY
      - GITLAB
      type: string
      description: |-
        * `NONE` - None
        * `STALE` - Stale
        * `GITHUB` - Github
        * `UNHEALTHY` - Unhealthy
        * `GITLAB` - Gitlab
    Telemetry:
      type: object
      properties:
        organisations:
          type: integer
        projects:
          type: integer
        environments:
          type: integer
        features:
          type: integer
        segments:
          type: integer
        users:
          type: integer
        debug_enabled:
          type: boolean
        env:
          type: string
      required:
      - debug_enabled
      - env
      - environments
      - features
      - organisations
      - projects
      - segments
      - users
    TestWebhook:
      type: object
      properties:
        webhook_url:
          type: string
          format: uri
        scope:
          $ref: '#/components/schemas/Scope'
        secret:
          type:
          - string
          - 'null'
      required:
      - scope
      - webhook_url
    TestWebhookErrorResponse:
      type: object
      properties:
        detail:
          type: string
        status:
          type: integer
        body:
          type:
          - string
          - 'null'
      required:
      - detail
      - status
    TestWebhookSuccessResponse:
      type: object
      properties:
        detail:
          type: string
        status:
          type: integer
          default: 200
      required:
      - detail
    TokenCreate:
      type: object
      properties:
        password:
          type: string
        email:
          type: string
    Trait:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        trait_key:
          type: string
          maxLength: 200
        value_type:
          oneOf:
          - $ref: '#/components/schemas/ValueTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        integer_value:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
        string_value:
          type:
          - string
          - 'null'
          maxLength: 2000
        boolean_value:
          type:
          - boolean
          - 'null'
        float_value:
          type:
          - number
          - 'null'
          format: double
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
      required:
      - trait_key
    TraitKeys:
      type: object
      properties:
        keys:
          type: array
          items:
            type: string
      required:
      - keys
    Type975Enum:
      enum:
      - int
      - unicode
      - bool
      type: string
      description: |-
        * `int` - Integer
        * `unicode` - String
        * `bool` - Boolean
    TypeD77Enum:
      enum:
      - STANDARD
      - MULTIVARIATE
      type: string
      description: |-
        * `STANDARD` - STANDARD
        * `MULTIVARIATE` - MULTIVARIATE
    UTMData:
      type: object
      properties:
        utm_source:
          type: string
        utm_medium:
          type: string
        utm_campaign:
          type: string
        utm_term:
          type: string
        utm_content:
          type: string
    UpdateEnvironment:
      type: object
      description: |-
        Mixin to add read only status to fields in a given serializer based on the existence
        of a subscription and a black list of plan ids

        Example usage:

            class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
                class Meta:
                    model = MyModel
                    fields = ("my_field",)

                invalid_plans = ("free",)
                field_names = ("my_field",)

                def get_subscription(self):
                    return subscription
      properties:
        id:
          type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          maxLength: 2000
        api_key:
          type: string
          maxLength: 100
        description:
          type:
          - string
          - 'null'
          maxLength: 20000
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove all previous Feature
            States for the previously associated projects Features that are related
            to this Environment. New default Feature States will be created for the
            new selected projects Features for this Environment.
        minimum_change_request_approvals:
          type:
          - integer
          - 'null'
          maximum: 2147483647
          minimum: -2147483648
          readOnly: true
        allow_client_traits:
          type: boolean
          description: Allows clients using the client API key to set traits.
        banner_text:
          type:
          - string
          - 'null'
          maxLength: 255
        banner_colour:
          type:
          - string
          - 'null'
          description: hex code for the banner colour
          maxLength: 7
        hide_disabled_flags:
          type:
          - boolean
          - 'null'
          description: 'If true will exclude flags from SDK which are disabled. NOTE:
            If set, this will override the project `hide_disabled_flags`'
        use_mv_v2_evaluation:
          type: boolean
          description: |-
            To avoid breaking the API, we return this field as well.

            Warning: this will still mean that sending the `use_mv_v2_evaluation` field
            (e.g. in a PUT request) will not behave as expected but, since this is a minor
            issue, I think we can ignore.
          readOnly: true
        use_identity_composite_key_for_hashing:
          type: boolean
          description: Enable this to have consistent multivariate and percentage
            split evaluations across all SDKs (in local and server side mode)
        hide_sensitive_data:
          type: boolean
          description: 'If true, will hide sensitive data(e.g: traits, description
            etc) from the SDK endpoints'
        use_v2_feature_versioning:
          type: boolean
          readOnly: true
        use_identity_overrides_in_local_eval:
          type: boolean
          description: When enabled, identity overrides will be included in the environment
            document
        is_creating:
          type: boolean
          readOnly: true
          description: Attribute used to indicate when an environment is still being
            created (via clone for example)
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
      required:
      - name
    UpdateFeature:
      type: object
      description: prevent users from changing certain values after creation
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          readOnly: true
        type:
          oneOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          - $ref: '#/components/schemas/BlankEnum'
        default_enabled:
          type: boolean
          readOnly: true
        initial_value:
          type:
          - string
          - 'null'
          readOnly: true
        created_date:
          type: string
          format: date-time
          readOnly: true
          title: DateCreated
        description:
          type:
          - string
          - 'null'
        tags:
          type: array
          items:
            type: integer
        multivariate_options:
          type: array
          items:
            $ref: '#/components/schemas/NestedMultivariateFeatureOption'
        is_archived:
          type: boolean
        owners:
          type: array
          items:
            type: integer
          readOnly: true
        group_owners:
          type: array
          items:
            type: integer
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        project:
          type: integer
          readOnly: true
          description: Changing the project selected will remove previous Feature
            States for the previously associated projects Environments that are related
            to this Feature. New default Feature States will be created for the new
            selected projects Environments for this Feature. Also this will remove
            any Tags associated with a feature as Tags are Project defined
        environment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        segment_feature_state:
          oneOf:
          - $ref: '#/components/schemas/FeatureStateSerializerSmall'
          - type: 'null'
          readOnly: true
        num_segment_overrides:
          type: integer
          readOnly: true
          description: Number of segment overrides that exist for the given feature
            in the environment provided by the `environment` query parameter.
        num_identity_overrides:
          type:
          - integer
          - 'null'
          readOnly: true
          description: 'Number of identity overrides that exist for the given feature
            in the environment provided by the `environment` query parameter. Note:
            will return null for Edge enabled projects.'
        is_num_identity_overrides_complete:
          type: boolean
          readOnly: true
          default: true
        is_server_key_only:
          type: boolean
        last_modified_in_any_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the given project. Note: requires feature versioning
            v2 enabled on the environment.'
        last_modified_in_current_environment:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
          description: 'Datetime representing the last time that the feature was modified
            in any environment in the current environment. Note: requires that the
            environment query parameter is passed and feature versioning v2 enabled
            on the environment.'
        metadata:
          type: array
          items:
            $ref: '#/components/schemas/Metadata'
        code_references_counts:
          type: array
          items:
            $ref: '#/components/schemas/FeatureFlagCodeReferencesRepositoryCount'
          readOnly: true
    UpdateFlag:
      type: object
      properties:
        feature:
          $ref: '#/components/schemas/FeatureIdentifier'
        segment:
          $ref: '#/components/schemas/FeatureUpdateSegmentData'
        enabled:
          type: boolean
        value:
          $ref: '#/components/schemas/FeatureValue'
      required:
      - enabled
      - feature
      - value
    UpdateFlagV2:
      type: object
      properties:
        feature:
          $ref: '#/components/schemas/FeatureIdentifier'
        environment_default:
          $ref: '#/components/schemas/EnvironmentDefault'
        segment_overrides:
          type: array
          items:
            $ref: '#/components/schemas/SegmentOverride'
      required:
      - environment_default
      - feature
    UpdateSubscription:
      type: object
      properties:
        hosted_page_id:
          type: string
      required:
      - hosted_page_id
    UsageData:
      type: object
      properties:
        flags:
          type: integer
        identities:
          type: integer
        traits:
          type: integer
        environment_document:
          type: integer
        day:
          type: string
        labels:
          oneOf:
          - $ref: '#/components/schemas/Labels'
          - type: 'null'
      required:
      - day
      - environment_document
      - flags
      - identities
      - traits
    UsageTotalCount:
      type: object
      properties:
        count:
          type: integer
      required:
      - count
    User:
      type: object
      properties:
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        sign_up_type:
          oneOf:
          - $ref: '#/components/schemas/SignUpTypeEnum'
          - $ref: '#/components/schemas/BlankEnum'
          - $ref: '#/components/schemas/NullEnum'
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          readOnly: true
      required:
      - first_name
      - last_name
    UserDetailedPermissions:
      type: object
      properties:
        admin:
          type: boolean
        permissions:
          type: array
          items:
            $ref: '#/components/schemas/DetailedPermissions'
        is_directly_granted:
          type: boolean
        derived_from:
          $ref: '#/components/schemas/DerivedFrom'
      required:
      - admin
      - derived_from
      - is_directly_granted
      - permissions
    UserId:
      type: object
      properties:
        id:
          type: integer
      required:
      - id
    UserIds:
      type: object
      properties:
        user_ids:
          type: array
          items:
            type: integer
      required:
      - user_ids
    UserList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          maxLength: 254
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        last_login:
          type:
          - string
          - 'null'
          format: date-time
        uuid:
          type: string
          format: uuid
          readOnly: true
      required:
      - email
      - first_name
      - last_name
    UserObjectPermissions:
      type: object
      properties:
        permissions:
          type: array
          items:
            type: string
        admin:
          type: boolean
        tag_based_permissions:
          type: array
          items:
            $ref: '#/components/schemas/TagBasedPermission'
      required:
      - admin
      - permissions
      - tag_based_permissions
    UserOrganisation:
      type: object
      properties:
        role:
          $ref: '#/components/schemas/RoleEnum'
        organisation:
          allOf:
          - $ref: '#/components/schemas/OrganisationSerializerBasic'
          readOnly: true
      required:
      - role
    UserOrganisationPermissionList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        user:
          $ref: '#/components/schemas/UserList'
        permissions:
          type: array
          items:
            type: string
      required:
      - user
    UserOrganisationPermissionUpdateCreate:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        user:
          type: integer
        permissions:
          type: array
          items:
            type: string
      required:
      - user
    UserPermissionGroup:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 200
        users:
          type: array
          items:
            type: integer
          readOnly: true
        is_default:
          type: boolean
          description: If set to true, all new users will be added to this group
        external_id:
          type:
          - string
          - 'null'
          description: Unique ID of the group in an external system
          maxLength: 255
      required:
      - name
    UserPermissionGroupMembership:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        email:
          type: string
          format: email
          maxLength: 254
        first_name:
          type: string
          maxLength: 150
        last_name:
          type: string
          maxLength: 150
        last_login:
          type:
          - string
          - 'null'
          format: date-time
        group_admin:
          type: boolean
          readOnly: true
      required:
      - email
      - first_name
      - last_name
    UserPermissionGroupOrganisationPermissionList:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        group:
          $ref: '#/components/schemas/UserPermissionGroup'
        permissions:
          type: array
          items:
            type: string
      required:
      - group
    UserPermissionGroupOrganisationPermissionUpdateCreate:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        group:
          type: integer
        permissions:
          type: array
          items:
            type: string
      required:
      - group
    UserPermissionGroupSerializerDetail:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 200
        users:
          type: array
          items:
            $ref: '#/components/schemas/UserPermissionGroupMembership'
          readOnly: true
        is_default:
          type: boolean
          description: If set to true, all new users will be added to this group
        external_id:
          type:
          - string
          - 'null'
          description: Unique ID of the group in an external system
          maxLength: 255
      required:
      - name
    UserPermissionGroupSummary:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          readOnly: true
    UsernameResetConfirm:
      type: object
      properties:
        new_email:
          type: string
          format: email
          title: Email
          maxLength: 254
      required:
      - new_email
    V1EnvironmentDocumentResponse:
      description: |-
        `/api/v1/environment-documents/` response.

        Powers Flagsmith SDK's local evaluation mode.
      properties:
        api_key:
          title: Api Key
          type: string
        feature_states:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseFeatureState'
          title: Feature States
          type: array
        identity_overrides:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseIdentityOverride'
          title: Identity Overrides
          type: array
        name:
          title: Name
          type: string
        project:
          $ref: '#/components/schemas/V1EnvironmentDocumentResponseProject'
      required:
      - api_key
      - feature_states
      - identity_overrides
      - name
      - project
      title: V1EnvironmentDocumentResponse
      type: object
    V1EnvironmentDocumentResponseFeature:
      description: Represents a Flagsmith feature, defined at project level.
      properties:
        id:
          title: Id
          type: integer
        name:
          title: Name
          type: string
        type:
          allOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          title: Type
      required:
      - id
      - name
      - type
      title: Feature
      type: object
    V1EnvironmentDocumentResponseFeatureSegment:
      description: Represents data specific to a segment feature override.
      properties:
        priority:
          anyOf:
          - type: integer
          - type: 'null'
          title: Priority
      required:
      - priority
      title: FeatureSegment
      type: object
    V1EnvironmentDocumentResponseFeatureState:
      description: Used to define the state of a feature for an environment, segment
        overrides, and identity overrides.
      properties:
        feature:
          $ref: '#/components/schemas/V1EnvironmentDocumentResponseFeature'
        enabled:
          title: Enabled
          type: boolean
        feature_state_value:
          anyOf:
          - type: integer
          - type: boolean
          - type: string
          - type: 'null'
          title: Feature State Value
        featurestate_uuid:
          format: uuid
          title: Featurestate Uuid
          type: string
        feature_segment:
          anyOf:
          - $ref: '#/components/schemas/V1EnvironmentDocumentResponseFeatureSegment'
          - type: 'null'
        multivariate_feature_state_values:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseMultivariateFeatureStateValue'
          title: Multivariate Feature State Values
          type: array
      required:
      - feature
      - enabled
      - feature_state_value
      - featurestate_uuid
      - feature_segment
      - multivariate_feature_state_values
      title: FeatureState
      type: object
    V1EnvironmentDocumentResponseIdentityOverride:
      description: Represents an identity override, defining feature states specific
        to an identity.
      properties:
        identifier:
          title: Identifier
          type: string
        identity_features:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseFeatureState'
          title: Identity Features
          type: array
      required:
      - identifier
      - identity_features
      title: IdentityOverride
      type: object
    V1EnvironmentDocumentResponseMultivariateFeatureOption:
      description: Represents a single multivariate feature option in the Flagsmith
        UI.
      properties:
        value:
          title: Value
          type: string
      required:
      - value
      title: MultivariateFeatureOption
      type: object
    V1EnvironmentDocumentResponseMultivariateFeatureStateValue:
      description: Represents a multivariate feature state value.
      properties:
        id:
          anyOf:
          - type: integer
          - type: 'null'
          title: Id
        mv_fs_value_uuid:
          anyOf:
          - format: uuid
            type: string
          - type: 'null'
          title: Mv Fs Value Uuid
        percentage_allocation:
          title: Percentage Allocation
          type: number
        multivariate_feature_option:
          $ref: '#/components/schemas/V1EnvironmentDocumentResponseMultivariateFeatureOption'
      required:
      - id
      - mv_fs_value_uuid
      - percentage_allocation
      - multivariate_feature_option
      title: MultivariateFeatureStateValue
      type: object
    V1EnvironmentDocumentResponseProject:
      description: Represents a Flagsmith project. For SDKs, this is mainly used to
        convey segment data.
      properties:
        segments:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseSegment'
          title: Segments
          type: array
      required:
      - segments
      title: Project
      type: object
    V1EnvironmentDocumentResponseSegment:
      description: Represents a Flagsmith segment. Carries rules and feature overrides.
      properties:
        id:
          title: Id
          type: integer
        name:
          title: Name
          type: string
        rules:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseSegmentRule'
          title: Rules
          type: array
        feature_states:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseFeatureState'
          title: Feature States
          type: array
      required:
      - id
      - name
      - rules
      title: Segment
      type: object
    V1EnvironmentDocumentResponseSegmentCondition:
      description: Represents a condition within a segment rule used by Flagsmith
        engine.
      properties:
        operator:
          allOf:
          - $ref: '#/components/schemas/V1EnvironmentDocumentResponseSegmentConditionOperatorEnum'
          title: Operator
        value:
          title: Value
          type: string
        property_:
          title: Property
          type: string
      required:
      - operator
      - value
      - property_
      title: SegmentCondition
      type: object
    V1EnvironmentDocumentResponseSegmentConditionOperatorEnum:
      enum:
      - EQUAL
      - GREATER_THAN
      - LESS_THAN
      - LESS_THAN_INCLUSIVE
      - CONTAINS
      - GREATER_THAN_INCLUSIVE
      - NOT_CONTAINS
      - NOT_EQUAL
      - REGEX
      - PERCENTAGE_SPLIT
      - MODULO
      - IS_SET
      - IS_NOT_SET
      - IN
      type: string
    V1EnvironmentDocumentResponseSegmentRule:
      description: Represents a rule within a segment used by Flagsmith engine. Root
        rules usually contain nested rules.
      properties:
        type:
          allOf:
          - $ref: '#/components/schemas/V1EnvironmentDocumentResponseSegmentRuleTypeEnum'
          title: Type
        rules:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseSegmentRule'
          title: Rules
          type: array
        conditions:
          items:
            $ref: '#/components/schemas/V1EnvironmentDocumentResponseSegmentCondition'
          title: Conditions
          type: array
      required:
      - type
      - rules
      - conditions
      title: SegmentRule
      type: object
    V1EnvironmentDocumentResponseSegmentRuleTypeEnum:
      enum:
      - ALL
      - ANY
      - NONE
      type: string
    V1IdentitiesRequest:
      description: |-
        `/api/v1/identities/` request.

        Used to retrieve flags for an identity and store its traits.
      properties:
        identifier:
          title: Identifier
          type: string
        traits:
          anyOf:
          - items:
              $ref: '#/components/schemas/V1IdentitiesRequestTraitInput'
            type: array
          - type: 'null'
          title: Traits
        transient:
          anyOf:
          - type: boolean
          - type: 'null'
          title: Transient
      required:
      - identifier
      title: V1IdentitiesRequest
      type: object
    V1IdentitiesRequestTraitInput:
      description: Represents a key-value pair trait provided as input when creating
        or updating an identity.
      properties:
        trait_key:
          title: Trait Key
          type: string
        trait_value:
          anyOf:
          - type: integer
          - type: number
          - type: boolean
          - type: string
          - type: 'null'
          title: Trait Value
        transient:
          anyOf:
          - type: boolean
          - type: 'null'
          title: Transient
      required:
      - trait_key
      - trait_value
      title: TraitInput
      type: object
    V1IdentitiesResponse:
      description: |-
        `/api/v1/identities/` response.

        Represents the identity created or updated, along with its flags.
      properties:
        identifier:
          title: Identifier
          type: string
        flags:
          items:
            $ref: '#/components/schemas/V1IdentitiesResponseV1Flag'
          title: Flags
          type: array
        traits:
          items:
            $ref: '#/components/schemas/V1IdentitiesResponseTrait'
          title: Traits
          type: array
      required:
      - identifier
      - flags
      - traits
      title: V1IdentitiesResponse
      type: object
    V1IdentitiesResponseFeature:
      description: Represents a Flagsmith feature, defined at project level.
      properties:
        id:
          title: Id
          type: integer
        name:
          title: Name
          type: string
        type:
          allOf:
          - $ref: '#/components/schemas/TypeD77Enum'
          title: Type
      required:
      - id
      - name
      - type
      title: Feature
      type: object
    V1IdentitiesResponseTrait:
      description: Represents a key-value pair associated with an identity.
      properties:
        trait_key:
          title: Trait Key
          type: string
        trait_value:
          anyOf:
          - type: integer
          - type: number
          - type: boolean
          - type: string
          - type: 'null'
          title: Trait Value
      required:
      - trait_key
      - trait_value
      title: Trait
      type: object
    V1IdentitiesResponseV1Flag:
      description: Represents a single flag (feature state) returned by the Flagsmith
        SDK.
      properties:
        feature:
          $ref: '#/components/schemas/V1IdentitiesResponseFeature'
        enabled:
          title: Enabled
          type: boolean
        feature_state_value:
          anyOf:
          - type: integer
          - type: boolean
          - type: string
          - type: 'null'
          title: Feature State Value
      required:
      - feature
      - enabled
      - feature_state_value
      title: V1Flag
      type: object
    ValueTypeEnum:
      enum:
      - int
      - unicode
      - bool
      - float
      type: string
      description: |-
        * `int` - Integer
        * `unicode` - String
        * `bool` - Boolean
        * `float` - Float
    VcsProviderEnum:
      enum:
      - github
      type: string
      description: '* `github` - GitHub'
    WarehouseConnection:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        warehouse_type:
          $ref: '#/components/schemas/WarehouseTypeEnum'
        status:
          allOf:
          - $ref: '#/components/schemas/WarehouseConnectionStatusEnum'
          readOnly: true
        name:
          type: string
          maxLength: 255
        config:
          oneOf:
          - {}
          - type: 'null'
        created_at:
          type: string
          format: date-time
          readOnly: true
      required:
      - warehouse_type
    WarehouseConnectionStatusEnum:
      enum:
      - created
      - pending_connection
      - connected
      - errored
      type: string
      description: |-
        * `created` - Created
        * `pending_connection` - Pending Connection
        * `connected` - Connected
        * `errored` - Errored
    WarehouseTypeEnum:
      enum:
      - flagsmith
      - snowflake
      - clickhouse
      type: string
      description: |-
        * `flagsmith` - Flagsmith
        * `snowflake` - Snowflake
        * `clickhouse` - ClickHouse
    Webhook:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          maxLength: 200
        enabled:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        secret:
          type: string
          maxLength: 255
      required:
      - url
    WebhookConfiguration:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url:
          type: string
          maxLength: 200
        secret:
          type: string
          maxLength: 255
      required:
      - url
    WebhookScopeTypeEnum:
      enum:
      - organisation
      - environment
      type: string
      description: |-
        * `organisation` - organisation
        * `environment` - environment
    WritableNestedFeatureState:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        feature_state_value:
          $ref: '#/components/schemas/FeatureStateValue'
        multivariate_feature_state_values:
          type: array
          items:
            $ref: '#/components/schemas/MultivariateFeatureStateValue'
        identifier:
          type: string
          description: Can be passed as an alternative to `identity`
        deleted_at:
          type:
          - string
          - 'null'
          format: date-time
          readOnly: true
        uuid:
          type: string
          format: uuid
          readOnly: true
        enabled:
          type: boolean
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        live_from:
          type:
          - string
          - 'null'
          format: date-time
        version:
          type:
          - integer
          - 'null'
          readOnly: true
        feature:
          type: integer
        environment:
          type:
          - integer
          - 'null'
        identity:
          type:
          - integer
          - 'null'
        feature_segment:
          type:
          - integer
          - 'null'
        change_request:
          type:
          - integer
          - 'null'
        environment_feature_version:
          type:
          - string
          - 'null'
          format: uuid
      required:
      - environment
      - feature
    _CodeReferenceDetail:
      type: object
      properties:
        file_path:
          type: string
          maxLength: 4096
        line_number:
          type: integer
          minimum: 1
        scanned_at:
          type: string
          format: date-time
        vcs_provider:
          $ref: '#/components/schemas/VcsProviderEnum'
        repository_url:
          type: string
          format: uri
        revision:
          type: string
        permalink:
          type: string
          format: uri
      required:
      - file_path
      - line_number
      - permalink
      - repository_url
      - revision
      - scanned_at
      - vcs_provider
    _CodeReferenceSubmit:
      type: object
      properties:
        file_path:
          type: string
          maxLength: 4096
        line_number:
          type: integer
          minimum: 1
        feature_name:
          type: string
          maxLength: 100
      required:
      - feature_name
      - file_path
      - line_number
    _Identity:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        identifier:
          type: string
          maxLength: 2000
      required:
      - identifier
    _NestedSegmentRule:
      type: object
      description: Adds nested create feature
      properties:
        id:
          type: integer
          readOnly: true
        type:
          $ref: '#/components/schemas/SegmentRuleTypeEnum'
        conditions:
          type: array
          items:
            $ref: '#/components/schemas/Condition'
        delete:
          type: boolean
          writeOnly: true
      required:
      - type
  securitySchemes:
    Environment API Key:
      type: apiKey
      in: header
      name: X-Environment-Key
      description: For SDK endpoints. <a href='https://docs.flagsmith.com/clients/rest#public-api-endpoints'>Find
        out more</a>.
    Master API Key:
      type: apiKey
      in: header
      name: Authorization
      description: For Admin API endpoints. <a href='https://docs.flagsmith.com/clients/rest#private-api-endpoints'>Find
        out more</a>.
    basicAuth:
      type: http
      scheme: basic
    tokenAuth:
      type: apiKey
      in: header
      name: Authorization
      description: Token-based authentication with required prefix "Token"
tags:
- name: Authentication
  description: Authentication, MFA, OAuth, and token management.
- name: Organisations
  description: Manage organisations, users, groups, invites, and API keys.
- name: Projects
  description: Manage projects, tags, and imports/exports.
- name: Environments
  description: Manage environments, API keys, and metrics.
- name: Features
  description: Manage features and multivariate options.
- name: Feature states
  description: Manage feature states and feature versioning.
- name: Identities
  description: Manage identities and traits.
- name: Segments
  description: Manage segments and segment rules.
- name: Integrations
  description: Configure third-party integrations (Amplitude, DataDog, Slack, etc.).
- name: Permissions
  description: Manage user and group permissions across organisations, projects, and
    environments.
- name: Webhooks
  description: Manage webhooks for organisations and environments.
- name: Audit
  description: Access audit logs.
- name: Analytics
  description: SDK analytics and telemetry.
- name: Metadata
  description: Manage metadata fields and model configuration.
- name: Onboarding
  description: Onboarding flows.
- name: Admin dashboard
  description: Platform hub admin dashboard endpoints.
- name: sdk
  description: SDK endpoints for flags, identities, and traits.
- name: mcp
  description: MCP-compatible endpoints.
- name: experimental
  description: Experimental endpoints subject to change.
- name: Other
  description: Other endpoints.
