import Format from 'common/utils/format'
import { PlanLimit, usagePercent } from 'components/shared/UsageBar/utils'

export type MeterCopy = {
  /** The oversized figure: a percentage, or the count when there is no limit. */
  headline: string
  headlineCaption: string
  /** Appended to the total, so the total itself can stay emphasised. */
  fractionSuffix: string
  fractionCaption: string
}

const withLimit = (total: number, limit: number): MeterCopy => ({
  fractionCaption: 'API calls used / plan limit',
  fractionSuffix: ` / ${Format.shortenNumber(limit)}`,
  headline: `${usagePercent(total, limit)}%`,
  headlineCaption: 'of plan consumed',
})

const withoutLimit = (total: number): MeterCopy => ({
  fractionCaption: 'API calls used',
  fractionSuffix: '',
  headline: Format.shortenNumber(total),
  headlineCaption: 'API calls',
})

/**
 * Without a limit there is nothing to divide by, so the meter falls back to
 * reporting the raw count. One branch, so the two readings cannot drift apart.
 */
export const meterCopy = (total: number, limit: PlanLimit): MeterCopy =>
  limit ? withLimit(total, limit) : withoutLimit(total)
