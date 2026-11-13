import { Req } from 'common/types/requests'

export type AuditLogFilters = {
  search: string
}

export const DEFAULT_AUDIT_LOG_FILTERS: AuditLogFilters = {
  search: '',
}

// audit/serializers.py: search has min_length=3, shorter answers 400.
const MIN_SEARCH_LENGTH = 3

export const parseAuditLogFilters = (
  params: URLSearchParams,
): AuditLogFilters => ({ search: params.get('search') ?? '' })

export const serialiseAuditLogFilters = ({
  search,
}: AuditLogFilters): URLSearchParams => {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  return params
}

// The search the API will use, or nothing while it's too short to send.
export const getSentSearch = (search: string): string | undefined => {
  const trimmed = search.trim()
  return trimmed.length >= MIN_SEARCH_LENGTH ? trimmed : undefined
}

export const toOrganisationAuditLogParams = ({
  search,
}: AuditLogFilters): Omit<
  Req['getOrganisationAuditLogs'],
  'organisationId'
> => {
  const sent = getSentSearch(search)
  return sent ? { search: sent } : {}
}

export const hasActiveAuditLogFilters = ({ search }: AuditLogFilters) =>
  !!getSentSearch(search)
