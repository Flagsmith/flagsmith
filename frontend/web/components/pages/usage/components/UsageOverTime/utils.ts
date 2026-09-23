import moment from 'moment'
import { Res } from 'common/types/responses'
import { colorBorderDanger } from 'common/theme/tokens'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'

// date is the raw API day, day is the axis label.
export type DailyPoint = { date: string; day: string; total: number }
export type CumulativePoint = { date: string; day: string; cumulative: number }

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
    .map(([date, total]) => ({
      date,
      day: moment(date).format('D MMM'),
      total,
    }))
}

export const cumulativeTotals = (daily: DailyPoint[]): CumulativePoint[] => {
  let running = 0
  return daily.map((point) => {
    running += point.total
    return { cumulative: running, date: point.date, day: point.day }
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

export type ProjectedPoint = Omit<CumulativePoint, 'cumulative'> & {
  cumulative: number | null
  projected?: number
}

/** The last measured day carries both values, so the two lines meet. */
export const withProjection = (
  cumulative: CumulativePoint[],
  projectedTotal: number,
  periodEndsAt: string,
): ProjectedPoint[] => {
  const last = cumulative[cumulative.length - 1]
  if (!last) {
    return cumulative
  }

  const from = moment.utc(last.date).startOf('day')
  // periodEndsAt is exclusive, so the last day drawn is the one before it,
  // matching the range the billing strip shows.
  const end = moment.utc(periodEndsAt).subtract(1, 'millisecond').startOf('day')
  // Counted from the last measurement, not from today: usage data lags, and
  // anchoring on today would leave a gap and stretch the daily increment.
  const daysAhead = end.diff(from, 'days')

  if (!from.isValid() || daysAhead <= 0) {
    return cumulative
  }

  const step = (projectedTotal - last.cumulative) / daysAhead

  const future = Array.from({ length: daysAhead }, (_, index) => {
    const day = from.clone().add(index + 1, 'days')
    return {
      cumulative: null,
      date: day.format('YYYY-MM-DD'),
      day: day.format('D MMM'),
      projected: Math.round(last.cumulative + step * (index + 1)),
    }
  })

  return [
    ...cumulative.slice(0, -1),
    { ...last, projected: last.cumulative },
    ...future,
  ]
}
