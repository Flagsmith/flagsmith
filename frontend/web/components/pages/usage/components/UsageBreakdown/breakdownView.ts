import { UsageGroupBy } from 'common/types/requests'
import { Res } from 'common/types/responses'
import {
  BreakdownDimension,
  BreakdownRow,
  BreakdownStatus,
  byRequestType,
  bySdk,
  isGroupedDimension,
} from './utils'

export type QueryState = { isFetching: boolean; isError: boolean }

export const breakdownStatusOf = (
  groupBy: UsageGroupBy | undefined,
  queries: QueryState[],
  organisationLoaded: boolean,
): BreakdownStatus => {
  // Every query skips until the organisation loads, which would read as ready.
  if (!organisationLoaded) return 'loading'
  if (!groupBy) return 'needs-project'
  if (queries.some((query) => query.isFetching)) return 'loading'
  // A failed scope must not read as zero usage.
  if (queries.some((query) => query.isError)) return 'error'
  return 'ready'
}

// Only the failed ones: a retry that refetched usage would spend the
// usage-data allowance of five requests a minute.
export const retryFailed = (
  queries: { isError: boolean; refetch: () => unknown }[],
) =>
  queries.forEach((query) => {
    if (query.isError) query.refetch()
  })

export type BreakdownView = {
  rows: BreakdownRow[]
  status?: BreakdownStatus
  onRetry?: () => void
}

export const breakdownViewOf = (
  dimension: BreakdownDimension,
  data: Res['organisationUsage'] | undefined,
  grouped: BreakdownView | undefined,
): BreakdownView => {
  if (!isGroupedDimension(dimension)) {
    return { rows: dimension === 'sdk' ? bySdk(data) : byRequestType(data) }
  }
  return grouped ?? { rows: [], status: 'loading' }
}
