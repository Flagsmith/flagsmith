// eslint-disable-next-line @typescript-eslint/no-empty-interface

export type EdgePagedResponse<T> = PagedResponse<T> & {
  last_evaluated_key?: string
  pages?: (string | undefined)[]
}
export type Approval =
  | {
      user: number
    }
  | {
      group: number
    }
export type PagedResponse<T> = {
  count?: number
  next?: string
  previous?: string
  results: T[]
}
export type FlagsmithValue = string | number | boolean | null

export type FeatureVersionState = {
  enabled: boolean
  feature: number
  feature_state_value: FeatureStateValue
  feature_segment: null | FeatureState['feature_segment']
  multivariate_feature_state_values: Omit<MultivariateFeatureStateValue, 'id'>[]
  live_from: FeatureState['live_from']
}
export type Operator = {
  value: string | null
  label: string
  hideValue?: boolean
  warning?: string
  valuePlaceholder?: string
}
export type ChangeRequestSummary = {
  id: number
  readOnly: boolean
  created_at: string
  updated_at: string
  description: string
  user: number
  committed_at: string | null
  committed_by: number | null
  deleted_at: string | null
  live_from: string | null
}
export type SegmentCondition = {
  delete?: boolean
  description?: string
  operator: string
  property: string
  value: string | number | null
}
export type SegmentRule = {
  type: string
  rules: SegmentRule[]

  delete?: boolean
  conditions: SegmentCondition[]
}
export type Segment = {
  id: number
  rules: SegmentRule[]
  uuid: string
  name: string
  description: string
  project: string | number
  feature?: number
  metadata: Metadata[] | []
}
export type Environment = {
  id: number
  name: string
  api_key: string
  description?: string
  banner_text?: string
  banner_colour?: string
  project: number
  minimum_change_request_approvals?: number
  allow_client_traits: boolean
  hide_sensitive_data: boolean
  total_segment_overrides?: number
  use_v2_feature_versioning: boolean
  metadata: Metadata[] | []
}
export type Project = {
  id: number
  uuid: string
  name: string
  organisation: number
  hide_disabled_flags: boolean
  enable_dynamo_db: boolean
  migration_status: string
  use_edge_identities: boolean
  show_edge_identity_overrides_for_feature: boolean
  prevent_flag_defaults: boolean
  enable_realtime_updates: boolean
  max_segments_allowed?: number | null
  max_features_allowed?: number | null
  max_segment_overrides_allowed?: number | null
  total_features?: number
  stale_flags_limit_days?: number
  total_segments?: number
  environments: Environment[]
}
export type ImportStrategy = 'SKIP' | 'OVERWRITE_DESTRUCTIVE'

export type ExternalResource = {
  id?: number
  url: string
  type: string
  project: number
  status: null | string
  feature: number
}

export type ImportExportStatus = 'SUCCESS' | 'PROCESSING' | 'FAILED'

export type FeatureImport = {
  id: number
  status: ImportExportStatus
  strategy: string
  environment_id: number
  created_at: string
}

export type FeatureExport = {
  id: string
  name: string
  environment_id: string
  status: ImportExportStatus
  created_at: string
}
export type FeatureImportItem = {
  name: string
  default_enabled: boolean
  is_server_key_only: boolean
  initial_value: FlagsmithValue
  value: FlagsmithValue
  enabled: false
  multivariate: []
}
export type LaunchDarklyProjectImport = {
  id: number
  created_by: string
  created_at: string
  updated_at: string
  completed_at: string
  status: {
    requested_environment_count: number
    requested_flag_count: number
    result: string | null
    error_message: string | null
  }
  project: number
}

export type Issue = {
  url: string
  repository_url: string
  labels_url: string
  comments_url: string
  events_url: string
  html_url: string
  id: number
  number: number
  title: string
  state: string
  created_at: string
  updated_at: string
  closed_at: null | string
  body: string
  timeline_url: string
}

export type PullRequest = {
  url: string
  id: number
  html_url: string
  issue_url: string
  number: number
  state: string
  locked: boolean
  title: string
  body: string | null
  created_at: string
  updated_at: string
  closed_at: string | null
  merged_at: string | null
  draft: boolean
  comments_url: string
  statuses_url: string
}

export type GithubPaginatedRepos<T> = {
  total_count: number
  repository_selection: string
  repositories: T[]
}

export type Repository = {
  id: number
  node_id: string
  name: string
  full_name: string
  private: boolean
  owner: {
    login: string
    id: number
    node_id: string
    avatar_url: string
    gravatar_id: string
    url: string
    html_url: string
    followers_url: string
    following_url: string
    gists_url: string
    starred_url: string
    subscriptions_url: string
    organizations_url: string
    repos_url: string
    events_url: string
    received_events_url: string
    type: string
    site_admin: boolean
  }
  html_url: string
  description: string | null
  fork: boolean
  url: string
  forks_url: string
  keys_url: string
  collaborators_url: string
  teams_url: string
  hooks_url: string
  issue_events_url: string
  events_url: string
  assignees_url: string
  branches_url: string
  tags_url: string
  blobs_url: string
  git_tags_url: string
  git_refs_url: string
  trees_url: string
  statuses_url: string
  languages_url: string
  stargazers_url: string
  contributors_url: string
  subscribers_url: string
  subscription_url: string
  commits_url: string
  git_commits_url: string
  comments_url: string
  issue_comment_url: string
  contents_url: string
  compare_url: string
  merges_url: string
  archive_url: string
  downloads_url: string
  issues_url: string
  pulls_url: string
  milestones_url: string
  notifications_url: string
  labels_url: string
  releases_url: string
  deployments_url: string
  created_at: string
  updated_at: string
  pushed_at: string
  git_url: string
  ssh_url: string
  clone_url: string
  svn_url: string
  homepage: string | null
  size: number
  stargazers_count: number
  watchers_count: number
  language: string
  has_issues: boolean
  has_projects: boolean
  has_downloads: boolean
  has_wiki: boolean
  has_pages: boolean
  has_discussions: boolean
  forks_count: number
  mirror_url: string | null
  archived: boolean
  disabled: boolean
  open_issues_count: number
  license: string | null
  allow_forking: boolean
  is_template: boolean
  web_commit_signoff_required: boolean
  topics: string[]
  visibility: string
  forks: number
  open_issues: number
  watchers: number
  default_branch: string
  permissions: {
    admin: boolean
    maintain: boolean
    push: boolean
    triage: boolean
    pull: boolean
  }
}

export type GithubRepository = {
  id: number
  github_configuration: number
  project: number
  repository_owner: string
  repository_name: string
}

export type githubIntegration = {
  id: string
  installation_id: string
  organisation: string
}

export type User = {
  id: number
  email: string
  last_login?: string
  first_name: string
  last_name: string
  role: 'ADMIN' | 'USER'
  date_joined: string
}
export type GroupUser = Omit<User, 'role'> & {
  group_admin: boolean
}

export type ProjectSummary = Omit<Project, 'environments'>

export type UserGroupSummary = {
  external_id: string | null
  id: number
  is_default: boolean
  name: string
}

export type UserGroup = UserGroupSummary & {
  users: GroupUser[]
}

export type UserPermission = {
  user: User
  permissions: string[]
  admin: boolean
  id: number
  role?: number
}
export type GroupPermission = Omit<UserPermission, 'user'> & {
  group: UserGroup
}

export type AuditLogItem = {
  id: number
  created_date: string
  log: string
  author?: User
  environment?: Environment
  project: ProjectSummary
  related_object_id: number
  related_object_type:
    | 'FEATURE'
    | 'FEATURE_STATE'
    | 'ENVIRONMENT'
    | 'CHANGE_REQUEST'
    | 'SEGMENT'
    | 'EDGE_IDENTITY'
  is_system_event: boolean
}

export type AuditLogDetail = AuditLogItem & {
  change_details: {
    field: string
    old: FlagsmithValue
    new: FlagsmithValue
  }[]
}
export type Subscription = {
  id: number
  uuid: string
  subscription_id: string | null
  subscription_date: string
  plan: string | null
  max_seats: number
  max_api_calls: number
  cancellation_date: string | null
  customer_id: string
  payment_method: string
  notes: string | null
}

export type Organisation = {
  id: number
  name: string
  created_date: string
  webhook_notification_email: string | null
  num_seats: number
  subscription: Subscription
  role: string
  persist_trait_data: boolean
  block_access_to_admin: boolean
  restrict_project_create_to_admin: boolean
}
export type Identity = {
  id?: string
  identifier: string
  identity_uuid?: string
}

export type AvailablePermission = {
  key: string
  description: string
}

export type APIKey = {
  active: boolean
  created_at: string
  expires_at: string | null
  id: number
  key: string
  name: string
}

export type Tag = {
  id: number
  color: string
  description: string
  project: number
  label: string
  is_system_tag: boolean
  is_permanent: boolean
  type: 'STALE' | 'NONE'
}

export type MultivariateFeatureStateValue = {
  id: number
  multivariate_feature_option: number
  percentage_allocation: number
}

export type FeatureStateValue = {
  boolean_value: boolean | null
  float_value?: number | null
  integer_value?: boolean | null
  string_value: string
  type: string
}

export type MultivariateOption = {
  id: number
  uuid: string
  type: string
  integer_value?: number
  string_value: string
  boolean_value?: boolean
  default_percentage_allocation: number
}

export type FeatureType = 'STANDARD' | 'MULTIVARIATE'
export type TagStrategy = 'INTERSECTION' | 'UNION'

export type IdentityFeatureState = {
  feature: {
    id: number
    name: string
    type: FeatureType
  }
  enabled: boolean
  feature_state_value: FlagsmithValue
  segment: null
  overridden_by: string | null
  multivariate_feature_state_values?: {
    multivariate_feature_option: {
      value: number
    }
    percentage_allocation: number
  }[]
}

export type FeatureState = {
  id: number
  feature_state_value: FlagsmithValue
  multivariate_feature_state_values: MultivariateFeatureStateValue[]
  identity?: string
  uuid: string
  enabled: boolean
  created_at: string
  updated_at: string
  environment_feature_version: string
  version?: number
  live_from?: string
  feature: number
  environment: number
  feature_segment?: {
    id: number
    priority: number
    segment: number
    uuid: string
  }
  change_request?: number
  //Added by FE
  toRemove?: boolean
}

export type ProjectFlag = {
  created_date: string
  default_enabled: boolean
  description?: string
  id: number
  initial_value: FlagsmithValue
  is_archived: boolean
  is_server_key_only: boolean
  multivariate_options: MultivariateOption[]
  name: string
  num_identity_overrides: number | null
  num_segment_overrides: number | null
  owners: User[]
  owner_groups: UserGroupSummary[]
  metadata: Metadata[] | []
  project: number
  tags: number[]
  type: string
  uuid: string
}

export type FeatureListProviderData = {
  projectFlags: ProjectFlag[] | null
  environmentFlags: FeatureState[] | null
  error: boolean
  isLoading: boolean
}

export type FeatureListProviderActions = {
  toggleFlag: (
    index: number,
    environments: Environment[],
    comment: string | null,
    environmentFlags: FeatureState[],
    projectFlags: ProjectFlag[],
  ) => void
  removeFlag: (projectId: string, projectFlag: ProjectFlag) => void
}

export type AuthType = 'EMAIL' | 'GITHUB' | 'GOOGLE'

export type SignupType = 'NO_INVITE' | 'INVITE_EMAIL' | 'INVITE_LINK'

export type Invite = {
  id: number
  email: string
  date_created: string
  invited_by: User
  link: string
  permission_groups: number[]
}

export type InviteLink = {
  id: number
  hash: string
  date_created: string
  role: string
  expires_at: string | null
}

export type SubscriptionMeta = {
  max_seats: number | null
  max_api_calls: number | null
  max_projects: number | null
  payment_source: string | null
  chargebee_email: string | null
}

export type Account = {
  first_name: string
  last_name: string
  sign_up_type: SignupType
  id: number
  email: string
  auth_type: AuthType
  is_superuser: boolean
}
export type Role = {
  id: number
  name: string
  description?: string
  organisation: number
}

export type RolePermissionUser = {
  user: number
  role: number
  id: number
  role_name: string
}
export type RolePermissionGroup = {
  group: number
  role: number
  id: number
  role_name: string
}
export type ChangeRequest = {
  id: number
  created_at: string
  updated_at: string
  environment: number
  title: string
  description: string | number
  feature_states: FeatureState[]
  user: number
  committed_at: number | null
  committed_by: number | null
  deleted_at: null
  approvals: {
    id: number
    user: number
    approved_at: null | string
  }[]
  is_approved: boolean
  is_committed: boolean
  group_assignments: { group: number }[]
  environment_feature_versions: {
    uuid: string
    feature_states: FeatureState[]
  }[]
}
export type FeatureVersion = {
  created_at: string
  updated_at: string
  published: boolean
  live_from: string
  uuid: string
  is_live: boolean
  published_by: number | null
  created_by: number | null
}

export type Metadata = {
  id?: number
  model_field: number | string
  field_value: string
}

export type MetadataField = {
  id: number
  name: string
  type: string
  description: string
  organisation: number
}

export type ContentType = {
  [key: string]: any
  id: number
  app_label: string
  model: string
}

export type isRequiredFor = {
  content_type: number
  object_id: number
}

export type MetadataModelField = {
  id: string
  field: number
  content_type: number | string
  is_required_for: isRequiredFor[]
}

export type Res = {
  segments: PagedResponse<Segment>
  segment: Segment
  auditLogs: PagedResponse<AuditLogItem>
  organisations: PagedResponse<Organisation>
  projects: ProjectSummary[]
  project: Project
  environments: PagedResponse<Environment>
  organisationUsage: {
    totals: {
      flags: number
      environmentDocument: number
      identities: number
      traits: number
      total: number
    }
    events_list: {
      environment_document: number | null
      flags: number | null
      identities: number | null
      traits: number | null
      name: string
    }[]
  }
  identity: { id: string } //todo: we don't consider this until we migrate identity-store
  identities: EdgePagedResponse<Identity>
  permission: Record<string, boolean>
  availablePermissions: AvailablePermission[]
  tag: Tag
  tags: Tag[]
  account: Account
  userEmail: {}
  groupAdmin: { id: string }
  groups: PagedResponse<UserGroupSummary>
  group: UserGroup
  myGroups: PagedResponse<UserGroupSummary>
  createSegmentOverride: {
    id: number
    segment: number
    priority: number
    uuid: string
    environment: number
    feature: number
    feature_segment_value: {
      id: number
      environment: number
      enabled: boolean
      feature: number
      feature_state_value: FeatureStateValue
      deleted_at: string
      uuid: string
      created_at: string
      updated_at: string
      version: number
      live_from: string
      identity: string
      change_request: string
    }
    value: string
  }
  featureVersion: FeatureVersion
  versionFeatureState: FeatureState[]
  role: Role
  roles: PagedResponse<Role>
  rolePermission: PagedResponse<UserPermission>
  projectFlags: PagedResponse<ProjectFlag>
  projectFlag: ProjectFlag
  identityFeatureStatesAll: IdentityFeatureState[]
  createRolesPermissionUsers: RolePermissionUser
  rolesPermissionUsers: PagedResponse<RolePermissionUser>
  createRolePermissionGroup: RolePermissionGroup
  rolePermissionGroup: PagedResponse<RolePermissionGroup>
  getSubscriptionMetadata: { id: string }
  environment: Environment
  metadataModelFieldList: PagedResponse<MetadataModelField>
  metadataModelField: MetadataModelField
  metadataList: PagedResponse<MetadataField>
  metadataField: MetadataField
  launchDarklyProjectImport: LaunchDarklyProjectImport
  launchDarklyProjectsImport: LaunchDarklyProjectImport[]
  roleMasterApiKey: { id: number; master_api_key: string; role: number }
  masterAPIKeyWithMasterAPIKeyRoles: {
    id: string
    prefix: string
    roles: RolePermissionUser[]
  }
  userWithRoles: PagedResponse<Role>
  groupWithRole: PagedResponse<Role>
  changeRequests: PagedResponse<ChangeRequestSummary>
  groupSummaries: UserGroupSummary[]
  supportedContentType: ContentType[]
  externalResource: PagedResponse<ExternalResource>
  githubIntegrations: PagedResponse<githubIntegration>
  githubRepository: PagedResponse<GithubRepository> | { data: { id: string } }
  githubIssues: Issue[]
  githubPulls: PullRequest[]
  githubRepos: GithubPaginatedRepos<Repository>
  segmentPriorities: {}
  featureSegment: FeatureState['feature_segment']
  featureVersions: PagedResponse<FeatureVersion>
  users: User[]
  enableFeatureVersioning: { id: string }
  auditLogItem: AuditLogDetail
  featureExport: { id: string }
  featureExports: PagedResponse<FeatureExport>
  flagsmithProjectImport: { id: string }
  featureImports: PagedResponse<FeatureImport>
  serversideEnvironmentKeys: APIKey[]
  userGroupPermissions: GroupPermission[]
  identityFeatureStates: PagedResponse<FeatureState>
  cloneidentityFeatureStates: IdentityFeatureState
  featureStates: PagedResponse<FeatureState>
  // END OF TYPES
}
