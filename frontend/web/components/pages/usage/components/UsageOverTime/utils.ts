import moment from 'moment'
import { Res } from 'common/types/responses'
import { colorBorderDanger } from 'common/theme/tokens'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'

export type DailyPoint = { day: string; total: number }
export type CumulativePoint = { day: string; cumulative: number }

export const dailyTotals = (
  data: Res['organisationUsage'] | undefined,
): DailyPoint[] => {
  const byDay = new Map<string, number>()

  for (const event of data?.events_list ?? []) {
    const total =
      (event.flags ?? 0) +
      (event.identities ?? 0) +
      (event.traits ?? 0) +
      (event.environment_document ?? 0)
    byDay.set(event.day, (byDay.get(event.day) ?? 0) + total)
  }

  return [...byDay.entries()]
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([day, total]) => ({ day: moment(day).format('D MMM'), total }))
}

export const cumulativeTotals = (daily: DailyPoint[]): CumulativePoint[] => {
  let running = 0
  return daily.map((point) => {
    running += point.total
    return { cumulative: running, day: point.day }
  })
}

export const planLimitThreshold = (limit: PlanLimit) =>
  limit
    ? {
        colour: colorBorderDanger,
        label: `Plan limit · ${Format.shortenNumber(limit)}`,
        value: limit,
      }
    : undefined

export const xAxisIntervalFor = (pointCount: number) =>
  Math.max(0, Math.ceil(pointCount / 12) - 1)
