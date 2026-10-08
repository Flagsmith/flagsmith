import { useMemo } from 'react'
import { Res } from 'common/types/responses'
import type { UsageBreakdownProps } from './UsageBreakdown'
import {
  byRequestType,
  bySdk,
  BreakdownDimension,
  isGroupedDimension,
} from './utils'

export type BreakdownView = Pick<
  UsageBreakdownProps,
  'rows' | 'status' | 'onRetry'
>

type UseUsageBreakdown = {
  data: Res['organisationUsage'] | undefined
  dimension: BreakdownDimension
  grouped: BreakdownView | undefined
}

export const useUsageBreakdown = ({
  data,
  dimension,
  grouped,
}: UseUsageBreakdown): BreakdownView => {
  const localRows = useMemo(
    () => (dimension === 'sdk' ? bySdk(data) : byRequestType(data)),
    [dimension, data],
  )

  if (!isGroupedDimension(dimension)) return { rows: localRows }
  return grouped ?? { rows: [], status: 'loading' }
}
