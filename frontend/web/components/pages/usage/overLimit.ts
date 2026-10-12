import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import Format from 'common/utils/format'
import { cumulativeTotals, dailyTotals } from './components/UsageOverTime/utils'
import { LimitStatusKind } from './limitStatus'
import { apiCallsWord, joinSentences } from './usageText'

export type OverLimit = {
  limit: number
  overBy: number
  /** Undefined when the rows do not cover the crossing. */
  crossedOn: string | undefined
}

// Same running total the chart draws, so the two cannot disagree.
export const limitCrossedOn = (
  data: Res['organisationUsage'] | undefined,
  limit: PlanLimit,
): string | undefined =>
  limit
    ? cumulativeTotals(dailyTotals(data)).find(
        (point) => point.cumulative >= limit,
      )?.day
    : undefined

export const overLimitOf = (
  total: number,
  limit: PlanLimit,
  data: Res['organisationUsage'] | undefined,
): OverLimit | undefined =>
  limit && total > limit
    ? { crossedOn: limitCrossedOn(data, limit), limit, overBy: total - limit }
    : undefined

const OVERAGE_NOTE: Partial<Record<LimitStatusKind, string>> = {
  'overage-charged': 'Charged at the overage rate.',
  'overage-covered': 'Covered as your first overage.',
}

export const overLimitNote = (
  over: OverLimit,
  status?: LimitStatusKind,
): string =>
  joinSentences(
    `${Format.shortenNumber(over.overBy)} ${apiCallsWord(
      over.overBy,
    )} over your ${Format.shortenNumber(over.limit)} limit.`,
    status && OVERAGE_NOTE[status],
  )
