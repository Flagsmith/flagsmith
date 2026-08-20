import moment from 'moment'
import { Res } from 'common/types/responses'
import { colorBorderDanger } from 'common/theme/tokens'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'

export type DailyPoint = { day: string; total: number }
export type CumulativePoint = { day: string; cumulative: number }

/**
 * The API returns one row per day and client type, so the rows have to be
 * summed by day first or a day with several client types draws several bars.
 * Sorted on the raw date, because the formatted label does not sort.
 */
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

/** Running total, so a billing period can be read against its ceiling. */
export const cumulativeTotals = (daily: DailyPoint[]): CumulativePoint[] => {
  let running = 0
  return daily.map((point) => {
    running += point.total
    return { cumulative: running, day: point.day }
  })
}

/**
 * Drawn as a ceiling on the cumulative chart. Nothing to draw without a limit.
 * Uses the border token, not the text one: the text intents are darkened in
 * light mode for contrast and shift between themes.
 */
export const planLimitThreshold = (limit: PlanLimit) =>
  limit
    ? {
        colour: colorBorderDanger,
        label: `Plan limit · ${Format.shortenNumber(limit)}`,
        value: limit,
      }
    : undefined

/** Keeps the axis readable by thinning the labels on long periods. */
export const xAxisIntervalFor = (pointCount: number) =>
  Math.max(0, Math.ceil(pointCount / 12) - 1)
