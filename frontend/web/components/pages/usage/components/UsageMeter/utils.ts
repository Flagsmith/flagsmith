import Format from 'common/utils/format'
import {
  PlanLimit,
  toneFor,
  usagePercent,
  UsageTone,
} from 'components/shared/UsageBar/utils'

type MeterCopy = {
  headline: string
  headlineCaption: string
  fraction?: {
    value: string
    suffix?: string
    caption: string
  }
}

export const meterCopy = (total: number, limit: PlanLimit): MeterCopy =>
  limit
    ? {
        fraction: {
          caption: 'API calls used / plan limit',
          suffix: ` / ${Format.shortenNumber(limit)}`,
          value: Format.shortenNumber(total),
        },
        headline: `${usagePercent(total, limit)}%`,
        headlineCaption: 'of plan consumed',
      }
    : {
        headline: Format.shortenNumber(total),
        headlineCaption: 'API calls',
      }

export const meterTone = (
  total: number,
  limit: PlanLimit,
  warnAt: number,
): UsageTone | undefined =>
  limit ? toneFor(usagePercent(total, limit), warnAt) : undefined
