export const ADMIN_PERMISSION = 'ADMIN' as const
export const ADMIN_PERMISSION_DESCRIPTION = 'Administrator' as const

// Organization Permissions
enum OrganisationPermissionEnum {
  CREATE_PROJECT = 'CREATE_PROJECT',
  MANAGE_USERS = 'MANAGE_USERS',
  MANAGE_USER_GROUPS = 'MANAGE_USER_GROUPS',
}
export const OrganisationPermissionDescriptions = {
  [OrganisationPermissionEnum.CREATE_PROJECT]: 'Create project',
  [OrganisationPermissionEnum.MANAGE_USERS]: 'Manage users',
  [OrganisationPermissionEnum.MANAGE_USER_GROUPS]: 'Manage user groups',
} as const

export type OrganisationPermission =
  | OrganisationPermissionEnum
  | typeof ADMIN_PERMISSION
export const OrganisationPermission = OrganisationPermissionEnum

export type OrganisationPermissionDescription =
  | (typeof OrganisationPermissionDescriptions)[keyof typeof OrganisationPermissionDescriptions]
  | typeof ADMIN_PERMISSION_DESCRIPTION

// Project Permissions
enum ProjectPermissionEnum {
  VIEW_PROJECT = 'VIEW_PROJECT',
  CREATE_ENVIRONMENT = 'CREATE_ENVIRONMENT',
  DELETE_FEATURE = 'DELETE_FEATURE',
  CREATE_FEATURE = 'CREATE_FEATURE',
  MANAGE_SEGMENTS = 'MANAGE_SEGMENTS',
  VIEW_AUDIT_LOG = 'VIEW_AUDIT_LOG',
  MANAGE_TAGS = 'MANAGE_TAGS',
  MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS = 'MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS',
  APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS = 'APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS',
  CREATE_PROJECT_LEVEL_CHANGE_REQUESTS = 'CREATE_PROJECT_LEVEL_CHANGE_REQUESTS',
}
export const ProjectPermissionDescriptions = {
  [ProjectPermissionEnum.VIEW_PROJECT]: 'View project',
  [ProjectPermissionEnum.CREATE_ENVIRONMENT]: 'Create environment',
  [ProjectPermissionEnum.DELETE_FEATURE]: 'Delete feature',
  [ProjectPermissionEnum.CREATE_FEATURE]: 'Create feature',
  [ProjectPermissionEnum.MANAGE_SEGMENTS]: 'Manage segments',
  [ProjectPermissionEnum.VIEW_AUDIT_LOG]: 'View audit log',
  [ProjectPermissionEnum.MANAGE_TAGS]: 'Manage tags',
  [ProjectPermissionEnum.MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS]:
    'Manage project level change requests',
  [ProjectPermissionEnum.APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS]:
    'Approve project level change requests',
  [ProjectPermissionEnum.CREATE_PROJECT_LEVEL_CHANGE_REQUESTS]:
    'Create project level change requests',
} as const

export type ProjectPermission = ProjectPermissionEnum | typeof ADMIN_PERMISSION
export const ProjectPermission = ProjectPermissionEnum

export type ProjectPermissionDescription =
  | (typeof ProjectPermissionDescriptions)[keyof typeof ProjectPermissionDescriptions]
  | typeof ADMIN_PERMISSION_DESCRIPTION

// Environment Permissions
enum EnvironmentPermissionEnum {
  VIEW_ENVIRONMENT = 'VIEW_ENVIRONMENT',
  UPDATE_FEATURE_STATE = 'UPDATE_FEATURE_STATE',
  MANAGE_IDENTITIES = 'MANAGE_IDENTITIES',
  CREATE_CHANGE_REQUEST = 'CREATE_CHANGE_REQUEST',
  APPROVE_CHANGE_REQUEST = 'APPROVE_CHANGE_REQUEST',
  VIEW_IDENTITIES = 'VIEW_IDENTITIES',
  MANAGE_SEGMENT_OVERRIDES = 'MANAGE_SEGMENT_OVERRIDES',
}
export const EnvironmentPermissionDescriptions = {
  [EnvironmentPermissionEnum.VIEW_ENVIRONMENT]: 'View environment',
  [EnvironmentPermissionEnum.UPDATE_FEATURE_STATE]: 'Update feature state',
  [EnvironmentPermissionEnum.MANAGE_IDENTITIES]: 'Manage identities',
  [EnvironmentPermissionEnum.CREATE_CHANGE_REQUEST]: 'Create change request',
  [EnvironmentPermissionEnum.APPROVE_CHANGE_REQUEST]: 'Approve change request',
  [EnvironmentPermissionEnum.VIEW_IDENTITIES]: 'View identities',
  [EnvironmentPermissionEnum.MANAGE_SEGMENT_OVERRIDES]:
    'Manage segment overrides',
} as const

export type EnvironmentPermission =
  | EnvironmentPermissionEnum
  | typeof ADMIN_PERMISSION
export const EnvironmentPermission = EnvironmentPermissionEnum

export type EnvironmentPermissionDescription =
  | (typeof EnvironmentPermissionDescriptions)[keyof typeof EnvironmentPermissionDescriptions]
  | typeof ADMIN_PERMISSION_DESCRIPTION

export type Permission =
  | OrganisationPermission
  | ProjectPermission
  | EnvironmentPermission
  | typeof ADMIN_PERMISSION

// Combined permission descriptions record
export const PermissionDescriptions = {
  ...OrganisationPermissionDescriptions,
  ...ProjectPermissionDescriptions,
  ...EnvironmentPermissionDescriptions,
  [ADMIN_PERMISSION]: ADMIN_PERMISSION_DESCRIPTION,
} as const
