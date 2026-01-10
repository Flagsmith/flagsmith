import {
  Account,
  ExternalResource,
  FeatureState,
  FeatureStateValue,
  ImportStrategy,
  Approval,
  MultivariateOption,
  SAMLConfiguration,
  Segment,
  Tag,
  ProjectFlag,
  Environment,
  UserGroup,
  AttributeName,
  Identity,
  ProjectChangeRequest,
  Role,
  RolePermission,
  Webhook,
  IdentityTrait,
  Onboarding,
  StageTrigger,
  StageActionType,
  StageActionBody,
  ChangeRequest,
  TagStrategy,
} from './responses'
import { UtmsType } from './utms'

export type UpdateProjectBody = {
  name: string
  hide_disabled_flags?: boolean
  prevent_flag_defaults?: boolean
  enable_realtime_updates?: boolean
  minimum_change_request_approvals?: number | null
  stale_flags_limit_days?: number | null
  only_allow_lower_case_feature_names?: boolean
  feature_name_regex?: string | null
}

export type UpdateOrganisationBody = {
  name: string
  force_2fa?: boolean
  restrict_project_create_to_admin?: boolean
  webhook_notification_email?: string | null
}

export type UpdateFeatureStateBody = {
  enabled?: boolean
  feature_state_value?: FeatureStateValue
  multivariate_feature_state_values?: MultivariateOption[] | null
}

export type PagedRequest<T> = T & {
  page?: number
  page_size?: number
  q?: string
}
export type OAuthType = 'github' | 'saml' | 'google'
export type PermissionLevel = 'organisation' | 'project' | 'environment'
export enum PermissionRoleType {
  GRANTED = 'GRANTED',
  GRANTED_FOR_TAGS = 'GRANTED_FOR_TAGS',
  NONE = 'NONE',
}
export const billingPeriods = [
  {
    label: 'Current billing period',
    value: 'current_billing_period',
  },
  {
    label: 'Previous billing period',
    value: 'previous_billing_period',
  },
  { label: 'Last 90 days', value: '90_day_period' },
  { label: 'Last 30 days', value: undefined },
]
export const freePeriods = [
  { label: 'Last 90 days', value: '90_day_period' },
  { label: 'Last 30 days', value: undefined },
]
export type CreateVersionFeatureState = {
  environmentId: string
  featureId: number
  sha: string
  featureState: FeatureState
}
export type WithoutId<T> = Omit<
  T,
  | 'id'
  | 'uuid'
  | 'created_at'
  | 'updated_at'
  | 'user'
  | 'committed_at'
  | 'deleted_at'
>
export type LoginRequest = {
  email: string
  password: string
}
export type RegisterRequest = {
  email: string
  first_name: string
  last_name: string
  password: string
  superuser?: boolean
  organisation_name?: string
  marketing_consent_given?: boolean
  utm_data?: UtmsType
}
export enum SortOrder {
  ASC = 'ASC',
  DESC = 'DESC',
}
export interface StageActionRequest {
  action_type: StageActionType | ''
  action_body: StageActionBody
}

export interface ReleasePipelineRequest {
  project: number
  name: string
  description?: string
  stages: PipelineStageRequest[]
}

export interface UpdateReleasePipelineRequest extends ReleasePipelineRequest {
  id: number
}

export interface PipelineStageRequest {
  name: string
  environment: number
  order: number
  trigger: StageTrigger
  actions: StageActionRequest[]
}

export type Req = {
  getFeatureCodeReferences: {
    projectId: number
    featureId: number
  }
  getSegments: PagedRequest<{
    q?: string
    projectId: number
    identity?: number
    include_feature_specific?: boolean
  }>
  deleteSegment: { projectId: number; id: number }
  updateSegment: {
    projectId: number
    segment: Segment
  }
  createSegment: {
    projectId: number
    segment: Omit<Segment, 'id' | 'uuid' | 'project'>
  }
  cloneSegment: {
    projectId: number
    segmentId: number
    name: string
  }
  getAuditLogs: PagedRequest<{
    search?: string
    project: number
    environments?: number
  }>
  getOrganisations: {}
  getOrganisation: { id: number }
  updateOrganisation: { id: number; body: UpdateOrganisationBody }
  deleteOrganisation: { id: number }
  uploadOrganisationLicence: {
    id: number
    body: {
      licence_signature: File
      licence: File
    }
  }
  getProjects: {
    organisationId: number
  }
  getEnvironments: {
    projectId: number
  }
  getOrganisationUsage: {
    organisationId: number
    projectId?: number
    environmentId?: string
    billing_period?:
      | 'current_billing_period'
      | 'previous_billing_period'
      | '90_day_period'
  }
  getWebhooks: {
    environmentId: string
  }
  createWebhook: {
    environmentId: string
    enabled: boolean
    secret: string
    url: string
  }
  updateWebhook: {
    id: number
    environmentId: string
    enabled: boolean
    secret: string
    url: string
  }
  deleteWebhook: {
    id: number
    environmentId: string
  }
  deleteIdentity: {
    id: string
    environmentId: string
    isEdge: boolean
  }
  createIdentities: {
    isEdge: boolean
    environmentId: string
    identifiers: string[]
  }
  featureSegment: {
    segment: number
  }
  getIdentities: PagedRequest<{
    environmentId: string
    pageType?: 'NEXT' | 'PREVIOUS'
    dashboard_alias?: string
    pages?: (string | undefined)[] // this is needed for edge since it returns no paging info other than a key
    isEdge: boolean
  }>
  getPermission: { id: number; level: PermissionLevel }
  getAvailablePermissions: { level: PermissionLevel }
  getTag: { id: number }
  getHealthEvents: { projectId: number }
  dismissHealthEvent: { projectId: number; eventId: number }
  getHealthProviders: { projectId: number }
  createHealthProvider: { projectId: number; name: string }
  deleteHealthProvider: { projectId: number; name: string }
  updateTag: { projectId: number; tag: Tag }
  deleteTag: {
    id: number
    projectId: number
  }
  getTags: {
    projectId: number
  }
  createTag: { projectId: number; tag: Omit<Tag, 'id'> }
  getSegment: { projectId: number; id: number }
  updateAccount: Account
  deleteAccount: {
    current_password: string
    delete_orphan_organisations: boolean
  }
  updateUserEmail: { current_password: string; new_email: string }
  createGroupAdmin: {
    group: number
    user: number
    orgId: number
  }
  deleteGroupAdmin: {
    orgId: number
    group: number
    user: number
  }
  getGroups: PagedRequest<{
    orgId: number
  }>
  deleteGroup: { id: number; orgId: number }
  getGroup: { id: number; orgId: number }
  getMyGroups: PagedRequest<{
    orgId: number
  }>
  createSegmentOverride: {
    environmentId: string
    featureId: number
    enabled: boolean
    multivariate_feature_state_values: MultivariateOption[] | null
    feature_segment: {
      segment: number
    }
    feature_state_value: FeatureStateValue
  }
  getRoles: { organisation_id: number }
  createRole: {
    organisation_id: number
    description: string | null
    name: string
  }
  getUserInvites: {
    organisationId: number
  }
  createUserInvite: {
    organisationId: number
    invites: {
      email: string
      role: string
      permission_groups: number[]
    }[]
  }
  deleteUserInvite: {
    organisationId: number
    inviteId: number
  }
  resendUserInvite: {
    organisationId: number
    inviteId: number
  }
  getRole: { organisation_id: number; role_id: number }
  updateRole: {
    organisation_id: number
    role_id: number
    body: Role
  }
  deleteRole: { organisation_id: number; role_id: number }
  getRolePermissionEnvironment: {
    organisation_id: number
    role_id: number
    env_id: number
  }
  getRolePermissionProject: {
    organisation_id: number
    role_id: number
    project_id: number
  }
  getRolePermissionOrganisation: {
    organisation_id: number
    role_id: number
  }
  createRolePermission: {
    level: PermissionLevel
    body: {
      admin?: boolean
      permissions: RolePermission['permissions']
      project: number
      environment: number
    }
    organisation_id: number
    role_id: number
  }
  updateRolePermission: Req['createRolePermission'] & { id: number }
  deleteRolePermission: { organisation_id: number; role_id: number }

  getIdentityFeatureStatesAll: {
    environment: number
    user: string
  }
  getProjectFlags: {
    project: string
    environment?: number
    segment?: number
    search?: string | null
    releasePipelines?: number[]
    page?: number
    tag_strategy?: TagStrategy
    tags?: string
    is_archived?: boolean
    value_search?: string | null
    is_enabled?: boolean | null
    owners?: number[]
    group_owners?: number[]
    sort_field?: string
    sort_direction?: SortOrder
  }
  getProjectFlag: { project: number; id: number }
  getRolesPermissionUsers: { organisation_id: number; role_id: number }
  deleteRolesPermissionUsers: {
    organisation_id: number
    role_id: number
    user_id: number
    level?: string
  }
  createRolesPermissionUsers: {
    data: {
      user: number
    }
    organisation_id: number
    role_id: number
  }
  getRolePermissionGroup: {
    organisation_id: number
    role_id: number
  }
  updateRolePermissionGroup: { id: number; role_id: number }
  deleteRolePermissionGroup: {
    group_id: number
    organisation_id: number
    role_id: number
  }
  createRolePermissionGroup: {
    data: {
      group: number
    }
    organisation_id: number
    role_id: number
  }
  getGetSubscriptionMetadata: { id: number }
  getEnvironment: { id: number }
  getSubscriptionMetadata: { id: number }
  getMetadataModelFields: { organisation_id: number }
  getMetadataModelField: { organisation_id: number; id: number }
  updateMetadataModelField: {
    organisation_id: number
    id: number
    body: {
      content_type: number
      field: number
      is_required_for: {
        content_type: number
        object_id: number
      }[]
    }
  }
  deleteMetadataModelField: { organisation_id: number; id: number }
  createMetadataModelField: {
    organisation_id: number
    body: {
      content_type: number
      field: number
    }
  }
  getMetadataField: { organisation_id: number }
  getMetadataList: { organisation: number }
  updateMetadataField: {
    id: number
    body: {
      name: string
      type: string
      description: string
      organisation: number
    }
  }
  deleteMetadataField: { id: number }
  createMetadataField: {
    body: {
      description: string
      name: string
      organisation: number
      type: string
    }
  }

  getRoleMasterApiKey: { org_id: number; role_id: number; id: string }
  updateRoleMasterApiKey: { org_id: number; role_id: number; id: string }
  deleteRoleMasterApiKey: { org_id: number; role_id: number; id: string }
  createRoleMasterApiKey: { org_id: number; role_id: number }
  getMasterAPIKeyWithMasterAPIKeyRoles: { org_id: number; prefix: string }
  deleteMasterAPIKeyWithMasterAPIKeyRoles: {
    org_id: number
    prefix: string
    role_id: number
  }
  getRolesMasterAPIKeyWithMasterAPIKeyRoles: { org_id: number; prefix: string }
  createLaunchDarklyProjectImport: {
    project_id: number
    body: {
      project_key: string
      token: string
    }
  }
  createFeatureExport: {
    environment_id: string
    tag_ids?: number[]
  }
  getFeatureExport: {
    id: number
  }
  getFeatureExports: {
    projectId: number
  }
  createFlagsmithProjectImport: {
    environment_id: string
    strategy: ImportStrategy
    file: File
  }
  getFeatureImports: {
    projectId: number
  }
  getLaunchDarklyProjectImport: { project_id: number; import_id: number }
  getLaunchDarklyProjectsImport: { project_id: number }
  getUserWithRoles: { org_id: number; user_id: number }
  deleteUserWithRole: { org_id: number; user_id: number; role_id: number }
  getGroupWithRole: { org_id: number; group_id: number }
  deleteGroupWithRole: { org_id: number; group_id: number; role_id: number }
  createAndSetFeatureVersion: {
    projectId: number
    environmentId: number // Numeric ID for getFeatureStates query
    environmentApiKey?: string // API key for URL endpoints (optional for legacy store)
    featureId: number
    skipPublish?: boolean
    featureStates: FeatureState[]
    liveFrom?: string
  }
  createFeatureVersion: {
    environmentId: number // Numeric ID for URL
    featureId: number
    live_from?: string
    feature_states_to_create: Omit<FeatureState, 'id'>[]
    feature_states_to_update: Omit<FeatureState, 'id'>[]
    publish_immediately: boolean
    segment_ids_to_delete_overrides: number[]
  }
  publishFeatureVersion: {
    sha: string
    environmentId: string
    featureId: number
  }
  createVersionFeatureState: CreateVersionFeatureState
  deleteVersionFeatureState: CreateVersionFeatureState & { id: number }
  updateVersionFeatureState: CreateVersionFeatureState & {
    id: number
    uuid: string
  }
  getVersionFeatureState: {
    sha: string
    environmentId: number
    featureId: number
  }
  updateSegmentPriorities: { id: number; priority: number }[]
  deleteFeatureSegment: { id: number }
  getFeatureVersions: PagedRequest<{
    featureId: number
    environmentId: string
    is_live?: boolean
  }>
  getUsers: { organisationId: number }
  getFeatureVersion: {
    uuid: string
  }
  enableFeatureVersioning: {
    environmentId: string
  }
  getChangeRequests: PagedRequest<{
    search?: string
    environmentId: string
    feature_id?: number
    live_from_after?: string
    committed?: boolean
  }>
  updateChangeRequest: ChangeRequest
  getGroupSummaries: {
    orgId: number
  }
  getSupportedContentType: { organisation_id: number }
  getExternalResources: { project_id: number; feature_id: number }
  deleteExternalResource: {
    project_id: number
    feature_id: number
    external_resource_id: string
  }
  createExternalResource: {
    project_id: number
    feature_id: number
    body: ExternalResource
  }

  getGithubIntegration: {
    organisation_id: number
    id?: number
  }
  updateGithubIntegration: {
    organisation_id: number
    github_integration_id: number
  }
  deleteGithubIntegration: {
    organisation_id: number
    github_integration_id: number
  }
  createGithubIntegration: {
    organisation_id: number
    body: {
      installation_id: string
    }
  }
  getGithubRepositories: {
    organisation_id: number
    github_id: number
  }
  updateGithubRepository: {
    organisation_id: number
    github_id: number
    id: number
    body: {
      project: number
      repository_name: string
      repository_owner: string
      tagging_enabled: boolean
    }
  }
  deleteGithubRepository: {
    organisation_id: number
    github_id: number
    id: number
  }
  createGithubRepository: {
    organisation_id: number
    github_id: number
    body: {
      project: number
      repository_name: string
      repository_owner: string
    }
  }
  getGithubResources: PagedRequest<{
    organisation_id: number
    repo_name: string
    repo_owner: string
    github_resource: string
  }>
  getGithubRepos: { installation_id: string; organisation_id: number }
  getServersideEnvironmentKeys: { environmentId: string }
  deleteServersideEnvironmentKeys: { environmentId: string; id: string }
  createServersideEnvironmentKeys: {
    environmentId: string
    data: { name: string }
  }
  getAuditLogItem: {
    projectId: number
    id: string
  }
  getProject: { id: number }
  updateProject: { id: number; body: UpdateProjectBody }
  deleteProject: { id: number }
  migrateProject: { id: number }
  getProjectPermissions: { projectId: number }
  createGroup: {
    orgId: number
    data: Omit<UserGroup, 'id' | 'users'>
    users: UserGroup['users']
    usersToAddAdmin: number[] | null
  }
  getUserGroupPermission: { project_id: number }
  updateProjectFlag: {
    project_id: number
    feature_id: number
    body: ProjectFlag
  }
  createProjectFlag: {
    project_id: number
    body: ProjectFlag
  }
  removeProjectFlag: {
    project_id: number
    flag_id: number
  }
  updateEnvironment: { id: number; body: Environment }
  createCloneIdentityFeatureStates: {
    environment_id: string
    identity_id: string
    body: {
      source_identity_id?: string
      source_identity_uuid?: string
    }
  }
  updateGroup: Req['createGroup'] & {
    orgId: number
    data: UserGroup
    users: UserGroup['users']

    usersToAddAdmin: number[] | null
    usersToRemoveAdmin: number[] | null
    usersToRemove: number[] | null
  }
  createChangeRequest: {
    approvals: Approval[]
    live_from: string | undefined
    description: string
    multivariate_options: MultivariateOption[]
    title: string
  }
  getFeatureStates: {
    environment?: number
    feature?: number
  }
  getFeatureSegment: { id: number }
  getSamlConfiguration: { name: string }
  getSamlConfigurations: { organisation_id: number }
  getSamlConfigurationMetadata: { name: string }
  updateSamlConfiguration: { name: string; body: SAMLConfiguration }
  deleteSamlConfiguration: { name: string }
  createSamlConfiguration: SAMLConfiguration
  getSamlAttributeMapping: { saml_configuration_id: number }
  updateSamlAttributeMapping: {
    attribute_id: number
    body: {
      saml_configuration: number
      django_attribute_name: AttributeName
      idp_attribute_name: string
    }
  }
  deleteSamlAttributeMapping: { attribute_id: number }
  createSamlAttributeMapping: {
    body: {
      saml_configuration: number
      django_attribute_name: AttributeName
      idp_attribute_name: string
    }
  }
  updateIdentity: {
    environmentId: string
    data: Identity
  }
  getProjectChangeRequests: PagedRequest<{
    project_id: number
    segment_id?: number
    live_from_after?: string
    committed?: boolean
  }>
  getProjectChangeRequest: { project_id: number; id: string }
  updateProjectChangeRequest: {
    data: ProjectChangeRequest
    project_id: number
  }
  createProjectChangeRequest: {
    data: WithoutId<ProjectChangeRequest>
    project_id: number
  }
  actionProjectChangeRequest: {
    actionType: 'approve' | 'commit'
    project_id: number
    id: string
  }
  deleteProjectChangeRequest: { project_id: number; id: string }
  createAuditLogWebhooks: {
    organisationId: number
    data: Omit<Webhook, 'id' | 'created_at' | 'updated_at'>
  }
  getAuditLogWebhooks: { organisationId: number }
  updateAuditLogWebhooks: { organisationId: number; data: Webhook }
  deleteAuditLogWebhook: { organisationId: number; id: number }
  createIdentityTrait: {
    use_edge_identities: boolean
    environmentId: string
    identity: string
    data: IdentityTrait
  }
  getIdentityTraits: {
    use_edge_identities: boolean
    environmentId: string
    identity: string
  }
  updateIdentityTrait: {
    use_edge_identities: boolean
    environmentId: string
    identity: string
    data: IdentityTrait
  }
  deleteIdentityTrait: {
    environmentId: string
    identity: string
    use_edge_identities: boolean
    data: Omit<IdentityTrait, 'trait_value'>
  }
  getIdentitySegments: PagedRequest<{
    q?: string
    identity: string
    projectId: number
  }>
  getConversionEvents: PagedRequest<{ q?: string; environment_id: string }>
  getSplitTest: PagedRequest<{
    conversion_event_type_id: number
  }>
  testWebhook: {
    webhookUrl: string
    secret?: string
    scope: {
      type: 'environment' | 'organisation'
      id: number
    }
  }
  register: {
    first_name: string
    last_name: string
    email: string
    password: string
    contact_consent_given: boolean
    organisation_name: string
    superuser: boolean
  }
  getBuildVersion: {}
  createOnboardingSupportOptIn: {}
  getEnvironmentMetrics: { id: number }
  getUserEnvironmentPermissions: {
    environmentId: string
    userId: number
  }
  getUserPermissions: {
    id?: number
    userId: number | undefined
    level: PermissionLevel
  }
  getProfile: {
    id?: number
  }
  getUser: { id: number }
  updateOnboarding: Partial<Onboarding>
  getReleasePipelines: PagedRequest<{ projectId: number; order_by?: string }>
  getReleasePipeline: { projectId: number; pipelineId: number }
  createReleasePipeline: ReleasePipelineRequest
  updateReleasePipeline: UpdateReleasePipelineRequest
  getPipelineStages: PagedRequest<{
    projectId: number
    pipelineId: number
  }>
  getPipelineStage: {
    projectId: number
    pipelineId: number
    stageId: number
  }
  deleteReleasePipeline: {
    projectId: number
    pipelineId: number
  }
  addFeatureToReleasePipeline: {
    projectId: number
    pipelineId: number
    featureId: number
  }
  publishReleasePipeline: {
    projectId: number
    pipelineId: number
  }
  removeFeatureFromReleasePipeline: {
    projectId: number
    pipelineId: number
    featureId: number
  }
  cloneReleasePipeline: {
    projectId: number
    pipelineId: number
    name: string
  }
  getFeatureAnalytics: {
    project_id: number
    feature_id: number
    period: number
    environment_ids: string[]
  }
  getEnvironmentAnalytics: {
    project_id: number
    feature_id: number
    period: number
    environment_id: string
  }
  getFeatureList: {
    projectId: number
    environmentId: string
    page?: number
    page_size?: number
    search?: string | null
    tags?: string
    is_archived?: boolean
    is_enabled?: boolean | null
    owners?: string
    group_owners?: string
    value_search?: string
    tag_strategy?: TagStrategy
    sort_field?: string
    sort_direction?: 'ASC' | 'DESC'
  }
  updateFeatureState: {
    environmentId: string
    environmentFlagId: number
    body: UpdateFeatureStateBody
  }
  // END OF TYPES
}
