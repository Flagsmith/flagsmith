export type AuditLogErrorKind = 'forbidden' | 'unknown'

const hasStatus = (error: unknown): error is { status: unknown } =>
  typeof error === 'object' && error !== null && 'status' in error

// 403 for members who aren't admins, 404 for non-members.
export const getAuditLogErrorKind = (error: unknown): AuditLogErrorKind => {
  if (!hasStatus(error)) return 'unknown'
  if (error.status === 403 || error.status === 404) return 'forbidden'
  return 'unknown'
}
