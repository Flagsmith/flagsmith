import {
  Account,
  Segment,
  Tag,
  FeatureStateValue,
  FeatureState,
  Role,
  ImportStrategy,
  APIKey,
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
    orgId: string
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
  getRoles: { organisation_id: string }
  createRole: { organisation_id: string; body: Role }
  getRole: { organisation_id: string; role_id: string }
  updateRole: { organisation_id: string; role_id: string; body: Role }
  deleteRole: { organisation_id: string; role_id: string }
  getRolePermission: { organisation_id: string; role_id: string }
  updateRolePermission: { organisation_id: string; role_id: string }
  deleteRolePermission: { organisation_id: string; role_id: string }
  createRolePermission: { organisation_id: string; role_id: string }
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
  getRolesPermissionUsers: { organisation_id: string; role_id: string }
  deleteRolesPermissionUsers: {
    organisation_id: string
    role_id: string
    user_id: string
    level?: string
  }
  createRolesPermissionUsers: { organisation_id: string; role_id: string }
  getRolePermissionGroup: { id: string }
  updateRolePermissionGroup: { id: string }
  deleteRolePermissionGroup: { id: string }
  createRolePermissionGroup: { organisation_id: string; role_id: string }
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
  getUserWithRoles: { org_id: string; user_id: string }
  deleteUserWihRole: { org_id: string; user_id: string; role_id: string }
  getGroupWithRole: { org_id: string; group_id: string }
  deleteGroupWithRole: { org_id: string; group_id: string; role_id: string }
  createAndPublishFeatureVersion: {
    environmentId: string
    featureId: number
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
  getUserGroupPermission: { project_id: string }
  // END OF TYPES
}
