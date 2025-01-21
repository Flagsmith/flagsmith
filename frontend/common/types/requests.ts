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
  Role,
  RolePermission,
} from './responses'

export type PagedRequest<T> = T & {
  page?: number
  page_size?: number
  q?: string
}
export type OAuthType = 'github' | 'saml' | 'google'
export type PermissionLevel = 'organisation' | 'project' | 'environment'
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
  environmentId: number
  featureId: number
  sha: string
  featureState: FeatureState
}
export type Req = {
  getSegments: PagedRequest<{
    q?: string
    projectId: number | string
    identity?: number
    include_feature_specific?: boolean
  }>
  deleteSegment: { projectId: number | string; id: number }
  updateSegment: {
    projectId: number | string
    segment: Segment
  }
  createSegment: {
    projectId: number | string
    segment: Omit<Segment, 'id' | 'uuid' | 'project'>
  }
  getAuditLogs: PagedRequest<{
    search?: string
    project: string
    environments?: string
  }>
  getOrganisations: {}
  uploadOrganisationLicence: {
    id: number
    body: {
      licence_signature: File
      licence: File
    }
  }
  getProjects: {
    organisationId: string
  }
  getEnvironments: {
    projectId: string
  }
  getOrganisationUsage: {
    organisationId: string
    projectId?: string
    environmentId?: string
    billing_period?:
      | 'current_billing_period'
      | 'previous_billing_period'
      | '90_day_period'
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
  getPermission: { id: string; level: PermissionLevel }
  getAvailablePermissions: { level: PermissionLevel }
  getTag: { id: string }
  updateTag: { projectId: string; tag: Tag }
  deleteTag: {
    id: number
    projectId: string
  }
  getTags: {
    projectId: string
  }
  createTag: { projectId: string; tag: Omit<Tag, 'id'> }
  getSegment: { projectId: string; id: string }
  updateAccount: Account
  deleteAccount: {
    current_password: string
    delete_orphan_organisations: boolean
  }
  updateUserEmail: { current_password: string; new_email: string }
  createGroupAdmin: {
    group: number | string
    user: number | string
    orgId: number | string
  }
  deleteGroupAdmin: {
    orgId: number | string
    group: number | string
    user: number | string
  }
  getGroups: PagedRequest<{
    orgId: number
  }>
  deleteGroup: { id: number | string; orgId: number | string }
  getGroup: { id: string; orgId: string }
  getMyGroups: PagedRequest<{
    orgId: string
  }>
  createSegmentOverride: {
    environmentId: string
    featureId: string
    enabled: boolean
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
  getRole: { organisation_id: string; role_id: number }
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
    environment: string
    user: string
  }
  getProjectFlags: {
    project: string
    environmentId?: string
    tags?: string[]
    is_archived?: boolean
  }
  getProjectFlag: { project: string | number; id: string }
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
  getGetSubscriptionMetadata: { id: string }
  getEnvironment: { id: string }
  getSubscriptionMetadata: { id: string }
  getMetadataModelFields: { organisation_id: string }
  getMetadataModelField: { organisation_id: string; id: string }
  updateMetadataModelField: {
    organisation_id: string
    id: string
    body: {
      content_type: number
      field: number
      is_required_for: {
        content_type: number
        object_id: number
      }[]
    }
  }
  deleteMetadataModelField: { organisation_id: string; id: string | number }
  createMetadataModelField: {
    organisation_id: string
    body: {
      content_type: number | string
      field: string | number
    }
  }
  getMetadataField: { organisation_id: string }
  getMetadataList: { organisation: string }
  updateMetadataField: {
    id: string
    body: {
      name: string
      type: string
      description: string
      organisation: string
    }
  }
  deleteMetadataField: { id: string }
  createMetadataField: {
    body: {
      description: string
      name: string
      organisation: string
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
    project_id: string
    body: {
      project_key: string
      token: string
    }
  }
  createFeatureExport: {
    environment_id: string
    tag_ids?: (number | string)[]
  }
  getFeatureExport: {
    id: string
  }
  getFeatureExports: {
    projectId: string
  }
  createFlagsmithProjectImport: {
    environment_id: number | string
    strategy: ImportStrategy
    file: File
  }
  getFeatureImports: {
    projectId: string
  }
  getLaunchDarklyProjectImport: { project_id: string; import_id: string }
  getLaunchDarklyProjectsImport: { project_id: string }
  getUserWithRoles: { org_id: number; user_id: number }
  deleteUserWithRole: { org_id: number; user_id: number; role_id: number }
  getGroupWithRole: { org_id: number; group_id: number }
  deleteGroupWithRole: { org_id: number; group_id: number; role_id: number }
  createAndSetFeatureVersion: {
    projectId: number
    environmentId: number
    featureId: number
    skipPublish?: boolean
    featureStates: FeatureState[]
    liveFrom?: string
  }
  createFeatureVersion: {
    environmentId: number
    featureId: number
    live_from?: string
    feature_states_to_create: Omit<FeatureState, 'id'>[]
    feature_states_to_update: Omit<FeatureState, 'id'>[]
    publish_immediately: boolean
    segment_ids_to_delete_overrides: number[]
  }
  publishFeatureVersion: {
    sha: string
    environmentId: number
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
  getGroupSummaries: {
    orgId: string
  }
  getSupportedContentType: { organisation_id: string }
  getExternalResources: { project_id: string; feature_id: string }
  deleteExternalResource: {
    project_id: string
    feature_id: string
    external_resource_id: string
  }
  createExternalResource: {
    project_id: string
    feature_id: string
    body: ExternalResource
  }

  getGithubIntegration: {
    organisation_id: string
    id?: string
  }
  updateGithubIntegration: {
    organisation_id: string
    github_integration_id: string
  }
  deleteGithubIntegration: {
    organisation_id: string
    github_integration_id: string
  }
  createGithubIntegration: {
    organisation_id: string
    body: {
      installation_id: string
    }
  }
  getGithubRepositories: {
    organisation_id: string
    github_id: string
  }
  updateGithubRepository: {
    organisation_id: string
    github_id: string
    id: string
    body: {
      project: number
      repository_name: string
      repository_owner: string
      tagging_enabled: boolean
    }
  }
  deleteGithubRepository: {
    organisation_id: string
    github_id: string
    id: string
  }
  createGithubRepository: {
    organisation_id: string
    github_id: string
    body: {
      project: string
      repository_name: string
      repository_owner: string
    }
  }
  getGithubResources: PagedRequest<{
    organisation_id: string
    repo_name: string
    repo_owner: string
    github_resource: string
  }>
  getGithubRepos: { installation_id: string; organisation_id: string }
  getServersideEnvironmentKeys: { environmentId: string }
  deleteServersideEnvironmentKeys: { environmentId: string; id: string }
  createServersideEnvironmentKeys: {
    environmentId: string
    data: { name: string }
  }
  getAuditLogItem: {
    projectId: string
    id: string
  }
  getProject: { id: string }
  createGroup: {
    orgId: string
    data: Omit<UserGroup, 'id' | 'users'>
    users: UserGroup['users']
    usersToAddAdmin: number[] | null
  }
  getUserGroupPermission: { project_id: string }
  updateProjectFlag: {
    project_id: string | number
    feature_id: string | number
    body: ProjectFlag
  }
  createProjectFlag: {
    project_id: string | number
    body: ProjectFlag
  }
  updateEnvironment: { id: string; body: Environment }
  createCloneIdentityFeatureStates: {
    environment_id: string
    identity_id: string
    body: {
      source_identity_id?: string
      source_identity_uuid?: string
    }
  }
  updateGroup: Req['createGroup'] & {
    orgId: string
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
  getFeatureSegment: { id: string }
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
  getFeatureAnalytics: {
    project_id: string
    feature_id: string
    period: number
    environment_ids: string[]
  }
  // END OF TYPES
}
