import { OrganisationAuditLogQuery } from 'common/types/requests'
import {
  AuditLogScopeFilter,
  parseScope,
  writeScopeParams,
} from './auditLogScopeFilter'

export type AuditLogFilters = {
  search: string
  scope: AuditLogScopeFilter
}

export const DEFAULT_AUDIT_LOG_FILTERS: AuditLogFilters = {
  scope: { type: 'all' },
  search: '',
}

// audit/serializers.py: search is 3 to 256 characters, anything else answers 400.
const MIN_SEARCH_LENGTH = 3
const MAX_SEARCH_LENGTH = 256

export const parseAuditLogFilters = (
  params: URLSearchParams,
): AuditLogFilters => ({
  scope: parseScope(params),
  search: params.get('search') ?? '',
})

export const serialiseAuditLogFilters = ({
  scope,
  search,
}: AuditLogFilters): URLSearchParams => {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  writeScopeParams(params, scope)
  return params
}

export const getSentSearch = (search: string): string | undefined => {
  // By character, not UTF-16 unit, so an emoji is never cut in half. Trimmed
  // again after the cap, as the API trims before checking the minimum.
  const sent = Array.from(search.trim())
    .slice(0, MAX_SEARCH_LENGTH)
    .join('')
    .trim()
  return Array.from(sent).length >= MIN_SEARCH_LENGTH ? sent : undefined
}

export const toOrganisationAuditLogParams = ({
  scope,
  search,
}: AuditLogFilters): OrganisationAuditLogQuery => {
  const sent = getSentSearch(search)
  const base = sent ? { search: sent } : {}
  switch (scope.type) {
    case 'organisation':
      return { ...base, is_organisation_level: true }
    case 'project':
      return {
        ...base,
        environments: scope.environmentIds.length
          ? scope.environmentIds
          : undefined,
        project: scope.projectId,
      }
    default:
      return base
  }
}

export const hasActiveAuditLogFilters = ({ scope, search }: AuditLogFilters) =>
  !!getSentSearch(search) || scope.type !== 'all'

// The scope control clears itself, so Clear all is only needed once there's a search.
export const showsClearAll = ({ search }: AuditLogFilters) =>
  !!getSentSearch(search)
