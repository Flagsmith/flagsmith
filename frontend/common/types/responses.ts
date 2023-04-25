// eslint-disable-next-line @typescript-eslint/no-empty-interface
import UserGroupList from 'components/UserGroupList'

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
export type SegmentCondition = {
  operator: string
  property: string

  delete?: boolean
  value: string
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
  prevent_flag_defaults: boolean
  enable_realtime_updates: boolean
  environments: Environment[]
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
  boolean_value?: boolean
  float_value?: number
  integer_value?: boolean
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
  multivariate_options: MultivariateOption[]
  name: string
  num_identity_overrides: number | null
  num_segment_overrides: number | null
  owners: User[]
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
  groupAdmin: { id: string }
  groups: PagedResponse<UserGroupSummary>
  group: UserGroup
  // END OF TYPES
}
