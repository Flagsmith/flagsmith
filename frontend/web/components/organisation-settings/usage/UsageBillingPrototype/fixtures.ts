import moment from 'moment'
import {
  BreakdownDimension,
  BreakdownRow,
  UsagePoint,
  UsageView,
} from './types'

/**
 * PROTOTYPE (#8184). Fake data so every designed state can be demonstrated.
 *
 * Delete this file when the real endpoints land: nothing outside the
 * prototype folder imports it.
 */

export type ScenarioId =
  | 'live'
  | 'healthy'
  | 'approaching'
  | 'over-covered'
  | 'over-charged'
  | 'free-countdown'
  | 'free-restricted'
  | 'free-restricted-now'
  | 'over-200'

export const SCENARIOS: { id: ScenarioId; label: string }[] = [
  { id: 'live', label: 'Live data' },
  { id: 'healthy', label: 'Healthy' },
  { id: 'approaching', label: 'Approaching limit' },
  { id: 'over-covered', label: 'Over limit, grace covering' },
  { id: 'over-charged', label: 'Over limit, charged' },
  { id: 'over-200', label: 'Over limit, 200%+' },
  { id: 'free-countdown', label: 'Free, grace countdown' },
  { id: 'free-restricted', label: 'Free, restricted' },
  { id: 'free-restricted-now', label: 'Free, restricted immediately' },
]

// A day's share of the period, shaped so the cumulative line has a believable
// wobble rather than a straight ramp. Indexed by day % 7, weekends lighter.
const DAY_WEIGHTS = [1.08, 1.12, 1.05, 1.1, 0.98, 0.62, 0.58]

const buildSeries = (
  total: number,
  daysElapsed: number,
  periodStart: moment.Moment,
): UsagePoint[] => {
  const weightTotal = Array.from({ length: daysElapsed }).reduce(
    (acc: number, _, index) => acc + DAY_WEIGHTS[index % DAY_WEIGHTS.length],
    0,
  )
  let running = 0
  return Array.from({ length: daysElapsed }).map((_, index) => {
    running += total * (DAY_WEIGHTS[index % DAY_WEIGHTS.length] / weightTotal)
    return {
      cumulative: Math.round(running),
      day: periodStart.clone().add(index, 'days').format('YYYY-MM-DD'),
    }
  })
}

const split = (
  total: number,
  parts: { label: string; op?: string; share: number }[],
): BreakdownRow[] =>
  parts.map(({ label, op, share }) => ({
    label,
    op,
    value: Math.round(total * share),
  }))

// Obviously invented names, so nobody mistakes the demo for their own data.
const buildBreakdowns = (
  total: number,
): Record<BreakdownDimension, BreakdownRow[]> => ({
  environment: split(total, [
    { label: 'Production', share: 0.81 },
    { label: 'Staging', share: 0.13 },
    { label: 'Development', share: 0.06 },
  ]),
  project: split(total, [
    { label: 'Web app', share: 0.54 },
    { label: 'Mobile', share: 0.31 },
    { label: 'Internal tools', share: 0.15 },
  ]),
  'request-type': split(total, [
    { label: 'Flag evaluations', op: 'get-flags', share: 0.63 },
    {
      label: 'Identity flag evaluations',
      op: 'get-identity-flags',
      share: 0.24,
    },
    { label: 'Trait updates', op: 'set-identity-traits', share: 0.09 },
    {
      label: 'Environment bootstrap',
      op: 'get-environment-document',
      share: 0.04,
    },
  ]),
  sdk: split(total, [
    { label: 'JavaScript', op: 'flagsmith-js', share: 0.42 },
    { label: 'Python', op: 'flagsmith-python', share: 0.27 },
    { label: 'Java', op: 'flagsmith-java', share: 0.19 },
    { label: 'Go', op: 'flagsmith-go', share: 0.12 },
  ]),
})

type ScenarioInput = {
  daysOverLimit?: number
  restrictedImmediately?: boolean
  resumesAt?: string
  plan: UsageView['plan']
  limit: number
  percent: number
  periodDays: number
  daysElapsed: number
  grace: UsageView['grace']
  graceDaysLeft?: number
  restricted?: boolean
  overageCost?: number | null
}

const buildView = ({
  daysElapsed,
  daysOverLimit,
  grace,
  graceDaysLeft,
  limit,
  overageCost = null,
  percent,
  periodDays,
  plan,
  restricted = false,
  restrictedImmediately,
  resumesAt,
}: ScenarioInput): UsageView => {
  const total = Math.round((limit * percent) / 100)
  const periodStart = moment().subtract(daysElapsed - 1, 'days')
  const resetsAt = periodStart.clone().add(periodDays, 'days')

  return {
    breakdowns: buildBreakdowns(total),
    channels: { email: true, inApp: true },
    daysOverLimit,
    grace,
    graceDaysLeft,
    limit,
    notifications: [
      { enabled: true, percent: 75 },
      { enabled: true, percent: 100 },
    ],
    overLimitSince: daysOverLimit
      ? moment().subtract(daysOverLimit, 'days').format('D MMM')
      : undefined,
    overageCost,
    period: {
      daysRemaining: periodDays - daysElapsed,
      isBillingPeriod: true,
      label: `${periodStart.format('D MMM')} to ${resetsAt.format(
        'D MMM YYYY',
      )}`,
      // Rolling windows never reset, so they get no reset date.
      resetsAt: resetsAt.format('D MMM YYYY'),

      selectValue: 'current_billing_period',
    },

    plan,
    // Run rate to the end of the period. Deliberately null early on, which is
    // the rule #8188 has to settle.
    projected:
      daysElapsed >= 5 ? Math.round((total / daysElapsed) * periodDays) : null,
    restricted,
    restrictedImmediately,
    resumesAt,
    series: buildSeries(total, daysElapsed, periodStart),
    total,
  }
}

export const FIXTURES: Record<Exclude<ScenarioId, 'live'>, UsageView> = {
  approaching: buildView({
    daysElapsed: 24,
    grace: 'available',
    limit: 2_000_000,
    percent: 88,
    periodDays: 30,
    plan: 'paid',
  }),
  'free-countdown': buildView({
    daysElapsed: 22,
    daysOverLimit: 4,
    grace: 'countdown',
    graceDaysLeft: 4,
    limit: 50_000,
    percent: 112,
    periodDays: 30,
    plan: 'free',
  }),
  'free-restricted': buildView({
    daysElapsed: 27,
    daysOverLimit: 7,
    grace: 'restricted',
    limit: 50_000,
    percent: 137,
    periodDays: 30,
    plan: 'free',
    restricted: true,
  }),
  'free-restricted-now': buildView({
    daysElapsed: 24,
    daysOverLimit: 1,
    grace: 'restricted',
    limit: 50_000,
    percent: 121,
    periodDays: 30,
    plan: 'free',
    restricted: true,
    restrictedImmediately: true,
    resumesAt: 'the period resets',
  }),
  healthy: buildView({
    daysElapsed: 17,
    grace: 'available',
    limit: 2_000_000,
    percent: 62,
    periodDays: 30,
    plan: 'paid',
  }),
  'over-200': buildView({
    daysElapsed: 26,
    daysOverLimit: 13,
    grace: 'not-applied',
    limit: 2_000_000,
    overageCost: 2280,
    percent: 214,
    periodDays: 30,
    plan: 'paid',
  }),
  'over-charged': buildView({
    daysElapsed: 21,
    daysOverLimit: 9,
    grace: 'used',
    limit: 2_000_000,
    overageCost: 1340,
    percent: 128,
    periodDays: 30,
    plan: 'paid',
  }),
  'over-covered': buildView({
    daysElapsed: 19,
    daysOverLimit: 6,
    grace: 'covering',
    limit: 2_000_000,
    percent: 118,
    periodDays: 30,
    plan: 'paid',
  }),
}
