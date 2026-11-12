export type AuditLogErrorKind = 'forbidden' | 'timeout' | 'unknown'

const hasStatus = (
  error: unknown,
): error is { status: unknown; data?: unknown } =>
  typeof error === 'object' && error !== null && 'status' in error

// 403 for members who aren't admins, 404 for non-members.
// 503 with code statement_timeout when a search runs too long.
export const getAuditLogErrorKind = (error: unknown): AuditLogErrorKind => {
  if (!hasStatus(error)) return 'unknown'
  if (error.status === 403 || error.status === 404) return 'forbidden'
  const code =
    typeof error.data === 'object' &&
    error.data !== null &&
    'code' in error.data
      ? error.data.code
      : undefined
  if (error.status === 503 && code === 'statement_timeout') return 'timeout'
  return 'unknown'
}
