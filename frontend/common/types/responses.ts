// eslint-disable-next-line @typescript-eslint/no-empty-interface

export type EdgePagedResponse<T> = PagedResponse<T> & {
  last_evaluated_key?: string
  pages?: (string | undefined)[]
}
export type PagedResponse<T> = {
  count?: number
  next?: string
  previous?: string
  results: T[]
}
export type FlagsmithValue = string | number | boolean | null
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
}
export type Environment = {
  id: number
  name: string
  api_key: string
  description?: string
  project: number
  minimum_change_request_approvals?: number
  allow_client_traits: boolean
  hide_sensitive_data: boolean
  total_segment_overrides?: number
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
  total_segments?: number
  environments: Environment[]
}

export type ExternalResource = {
  id?: number
  url: string
  type: string
  project: number
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
  node_id: string
  number: number
  title: string
  user: User
  labels: any[]
  state: string
  locked: boolean
  assignee: null | any
  assignees: any[]
  milestone: null | any
  comments: number
  created_at: string
  updated_at: string
  closed_at: null | string
  author_association: string
  active_lock_reason: null | string
  body: string
  reactions: Reaction
  timeline_url: string
  performed_via_github_app: null | any
  state_reason: null | string
}

export type PullRequest = {
  url: string
  id: number
  node_id: string
  html_url: string
  diff_url: string
  patch_url: string
  issue_url: string
  number: number
  state: string
  locked: boolean
  title: string
  user: any[]
  body: string | null
  created_at: string
  updated_at: string
  closed_at: string | null
  merged_at: string | null
  merge_commit_sha: string | null
  assignee: User | null
  assignees: User[]
  requested_reviewers: User[]
  requested_teams: any[]
  labels: any[]
  milestone: any
  draft: boolean
  commits_url: string
  review_comments_url: string
  review_comment_url: string
  comments_url: string
  statuses_url: string
  head: {
    label: string
    ref: string
    sha: string
    user: User
    repo: Repo
  }
  base: {
    label: string
    ref: string
    sha: string
    user: User
    repo: Repo
  }
  _links: {
    self: { href: string }
    html: { href: string }
    issue: { href: string }
    comments: { href: string }
    review_comments: { href: string }
    review_comment: { href: string }
    commits: { href: string }
    statuses: { href: string }
  }
  author_association: string
  auto_merge: string | null
  active_lock_reason: string | null
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

export type User = {
  id: number
  email: string
  first_name: string
  last_name: string
  role: 'ADMIN' | 'USER'
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

export type Tag = {
  id: number
  color: string
  description: string
  project: number
  label: string
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

export type IdentityFeatureState = {
  feature: {
    id: number
    name: string
    type: FeatureType
  }
  enabled: boolean
  feature_state_value: FlagsmithValue
  segment: null
  multivariate_feature_state_values?: {
    multivariate_feature_option: {
      value: number
    }
    percentage_allocation: number
  }[]
}

export type FeatureState = {
  id: number
  feature_state_value: string
  multivariate_feature_state_values: MultivariateFeatureStateValue[]
  identity?: string
  uuid: string
  enabled: boolean
  created_at: string
  updated_at: string
  version?: number
  live_from?: string
  hide_from_client?: string
  feature: number
  environment: number
  feature_segment?: number
  change_request?: number
}

export type ProjectFlag = {
  created_date: Date
  default_enabled: boolean
  description?: string
  id: number
  initial_value: string
  is_archived: boolean
  is_server_key_only: boolean
  multivariate_options: MultivariateOption[]
  name: string
  num_identity_overrides: number | null
  num_segment_overrides: number | null
  owners: User[]
  owner_groups: UserGroupSummary[]
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
}

export type Res = {
  segments: PagedResponse<Segment>
  segment: Segment
  auditLogs: PagedResponse<AuditLogItem>
  organisations: PagedResponse<Organisation>
  projects: ProjectSummary[]
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
  roles: Role[]
  rolePermission: { id: string }

  projectFlags: PagedResponse<ProjectFlag>
  projectFlag: ProjectFlag
  identityFeatureStates: IdentityFeatureState[]
  rolesPermissionUsers: RolePermissionUser
  rolePermissionGroup: { id: string }
  getSubscriptionMetadata: { id: string }
  environment: Environment
  launchDarklyProjectImport: LaunchDarklyProjectImport
  launchDarklyProjectsImport: LaunchDarklyProjectImport[]
  userWithRoles: PagedResponse<Roles>
  groupWithRole: PagedResponse<Roles>
  changeRequests: PagedResponse<ChangeRequestSummary>
  groupSummaries: UserGroupSummary[]
  externalResource: PagedResponse<ExternalResource>
  featureExternalResource: { id: string }
  githubIntegration: { id: string }
  githubRepository: { id: string }
  githubIssues: Issue[]
  githubPulls: PullRequest[]
  githubRepos: GithubPaginatedRepos<Repository>
  // END OF TYPES
}
