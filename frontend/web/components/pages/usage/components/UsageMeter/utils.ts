import Format from 'common/utils/format'
import { PlanLimit, usagePercent } from 'components/shared/UsageBar/utils'

export type MeterCopy = {
  headline: string
  headlineCaption: string
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

export const meterCopy = (total: number, limit: PlanLimit): MeterCopy =>
  limit ? withLimit(total, limit) : withoutLimit(total)
