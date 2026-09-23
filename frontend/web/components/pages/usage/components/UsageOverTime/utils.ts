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

export type ProjectedPoint = CumulativePoint & { projected?: number }

/** The last measured day carries both values, so the two lines meet. */
export const withProjection = (
  cumulative: CumulativePoint[],
  projectedTotal: number,
  periodEndsAt: string,
): ProjectedPoint[] => {
  const last = cumulative[cumulative.length - 1]
  const end = moment.utc(periodEndsAt).startOf('day')
  const daysAhead = end.diff(moment.utc().startOf('day'), 'days')

  if (!last || daysAhead <= 0) {
    return cumulative
  }

  const step = (projectedTotal - last.cumulative) / daysAhead

  const future = Array.from({ length: daysAhead }, (_, index) => ({
    cumulative: null as unknown as number,
    day: moment
      .utc()
      .startOf('day')
      .add(index + 1, 'days')
      .format('D MMM'),
    projected: Math.round(last.cumulative + step * (index + 1)),
  }))

  return [
    ...cumulative.slice(0, -1),
    { ...last, projected: last.cumulative },
    ...future,
  ]
}
