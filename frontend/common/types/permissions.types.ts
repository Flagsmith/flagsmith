// Organization Permissions
export enum OrganisationPermission {
  CREATE_PROJECT = 'CREATE_PROJECT',
  MANAGE_USERS = 'MANAGE_USERS',
  MANAGE_USER_GROUPS = 'MANAGE_USER_GROUPS',
}
export const OrganisationPermissionDescriptions = {
  [OrganisationPermission.CREATE_PROJECT]: 'Create project',
  [OrganisationPermission.MANAGE_USERS]: 'Manage users',
  [OrganisationPermission.MANAGE_USER_GROUPS]: 'Manage user groups',
} as const

export type OrganisationPermissionDescription =
  | (typeof OrganisationPermissionDescriptions)[keyof typeof OrganisationPermissionDescriptions]
  | typeof ADMIN_PERMISSION_DESCRIPTION

export const ADMIN_PERMISSION = 'ADMIN' as const
export const ADMIN_PERMISSION_DESCRIPTION = 'Administrator' as const

// Project Permissions
export enum ProjectPermission {
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
  [ProjectPermission.VIEW_PROJECT]: 'View project',
  [ProjectPermission.CREATE_ENVIRONMENT]: 'Create environment',
  [ProjectPermission.DELETE_FEATURE]: 'Delete feature',
  [ProjectPermission.CREATE_FEATURE]: 'Create feature',
  [ProjectPermission.MANAGE_SEGMENTS]: 'Manage segments',
  [ProjectPermission.VIEW_AUDIT_LOG]: 'View audit log',
  [ProjectPermission.MANAGE_TAGS]: 'Manage tags',
  [ProjectPermission.MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS]:
    'Manage project level change requests',
  [ProjectPermission.APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS]:
    'Approve project level change requests',
  [ProjectPermission.CREATE_PROJECT_LEVEL_CHANGE_REQUESTS]:
    'Create project level change requests',
} as const

export type ProjectPermissionDescription =
  | (typeof ProjectPermissionDescriptions)[keyof typeof ProjectPermissionDescriptions]
  | typeof ADMIN_PERMISSION_DESCRIPTION

// Environment Permissions
export enum EnvironmentPermission {
  VIEW_ENVIRONMENT = 'VIEW_ENVIRONMENT',
  UPDATE_FEATURE_STATE = 'UPDATE_FEATURE_STATE',
  MANAGE_IDENTITIES = 'MANAGE_IDENTITIES',
  CREATE_CHANGE_REQUEST = 'CREATE_CHANGE_REQUEST',
  APPROVE_CHANGE_REQUEST = 'APPROVE_CHANGE_REQUEST',
  VIEW_IDENTITIES = 'VIEW_IDENTITIES',
  MANAGE_SEGMENT_OVERRIDES = 'MANAGE_SEGMENT_OVERRIDES',
}
export const EnvironmentPermissionDescriptions = {
  [EnvironmentPermission.VIEW_ENVIRONMENT]: 'View environment',
  [EnvironmentPermission.UPDATE_FEATURE_STATE]: 'Update feature state',
  [EnvironmentPermission.MANAGE_IDENTITIES]: 'Manage identities',
  [EnvironmentPermission.CREATE_CHANGE_REQUEST]: 'Create change request',
  [EnvironmentPermission.APPROVE_CHANGE_REQUEST]: 'Approve change request',
  [EnvironmentPermission.VIEW_IDENTITIES]: 'View identities',
  [EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES]: 'Manage segment overrides',
} as const

export type EnvironmentPermissionDescription =
  | (typeof EnvironmentPermissionDescriptions)[keyof typeof EnvironmentPermissionDescriptions]
  | typeof ADMIN_PERMISSION_DESCRIPTION

export type Permission =
  | OrganisationPermission
  | ProjectPermission
  | EnvironmentPermission
  | typeof ADMIN_PERMISSION

export type PermissionDescription =
  | OrganisationPermissionDescription
  | ProjectPermissionDescription
  | EnvironmentPermissionDescription

// Combined permission descriptions record
export const PermissionDescriptions = {
  ...OrganisationPermissionDescriptions,
  ...ProjectPermissionDescriptions,
  ...EnvironmentPermissionDescriptions,
  [ADMIN_PERMISSION]: ADMIN_PERMISSION_DESCRIPTION,
} as const
