import {
  Account,
  ExternalResource,
  FeatureState,
  FeatureStateValue,
  ImportStrategy,
  Segment,
  Tag,
  UserGroup,
} from './responses'

export type PagedRequest<T> = T & {
  page?: number
  page_size?: number
  q?: string
}
export type OAuthType = 'github' | 'saml' | 'google'
export type PermissionLevel = 'organisation' | 'project' | 'environment'
export type CreateVersionFeatureState = {
  environmentId: string
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
  updateSegment: { projectId: number | string; segment: Segment }
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
    search?: string
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
    body: { description: string | null; name: string }
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
      permissions: string[]
      project: number
      environment: number
    }
    organisation_id: number
    role_id: number
  }
  updateRolePermission: Req['createRolePermission'] & { id: number }
  deleteRolePermission: { organisation_id: number; role_id: number }

  getIdentityFeatureStates: {
    environment: string
    user: string
  }
  getProjectFlags: {
    project: string
    environmentId?: string
    tags?: string[]
    is_archived?: boolean
  }
  getProjectFlag: { project: string; id: string }
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
    environmentId: string
    featureId: number
    skipPublish?: boolean
    featureStates: (FeatureState & { toRemove: boolean })[]
  }
  createFeatureVersion: {
    environmentId: string
    featureId: number
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
    environmentId: string
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
    environmentId: string
    featureId: string
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
  getGithubIssues: {
    organisation_id: string
    repo_name: string
    repo_owner: string
  }
  getGithubPulls: {
    organisation_id: string
    repo_name: string
    repo_owner: string
  }
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
  updateGroup: Req['createGroup'] & {
    orgId: string
    data: UserGroup
    users: UserGroup['users']

    usersToAddAdmin: number[] | null
    usersToRemoveAdmin: number[] | null
    usersToRemove: number[] | null
  }
  // END OF TYPES
}
