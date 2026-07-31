import moment from 'moment'
import { BreakdownRow, UsagePoint, UsageView } from './types'

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

export const SCENARIOS: { id: ScenarioId; label: string }[] = [
  { id: 'live', label: 'Live data' },
  { id: 'healthy', label: 'Healthy' },
  { id: 'approaching', label: 'Approaching limit' },
  { id: 'over-covered', label: 'Over limit, grace covering' },
  { id: 'over-charged', label: 'Over limit, charged' },
  { id: 'free-countdown', label: 'Free, grace countdown' },
  { id: 'free-restricted', label: 'Free, restricted' },
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

const buildBreakdown = (total: number): BreakdownRow[] => {
  // Split roughly as a real account does: flag evaluations dominate.
  const shares = [
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
  ]
  return shares.map(({ label, op, share }) => ({
    label,
    op,
    value: Math.round(total * share),
  }))
}

type ScenarioInput = {
  plan: UsageView['plan']
  limit: number
  percent: number
  periodDays: number
  daysElapsed: number
  grace: UsageView['grace']
  graceDaysLeft?: number
  restricted?: boolean
  overageCost?: number | null
  periodLabel?: string
  isBillingPeriod?: boolean
}

const buildView = ({
  daysElapsed,
  grace,
  graceDaysLeft,
  isBillingPeriod = true,
  limit,
  overageCost = null,
  percent,
  periodDays,
  periodLabel,
  plan,
  restricted = false,
}: ScenarioInput): UsageView => {
  const total = Math.round((limit * percent) / 100)
  const periodStart = moment().subtract(daysElapsed - 1, 'days')
  const resetsAt = periodStart.clone().add(periodDays, 'days')

  return {
    breakdown: buildBreakdown(total),
    channels: { email: true, inApp: true },
    grace,
    graceDaysLeft,
    limit,
    notifications: [
      { enabled: true, percent: 75 },
      { enabled: true, percent: 100 },
    ],
    overageCost,
    period: {
      daysRemaining: periodDays - daysElapsed,
      isBillingPeriod,
      label:
        periodLabel ??
        `${periodStart.format('D MMM')} to ${resetsAt.format('D MMM YYYY')}`,
      resetsAt: resetsAt.format('D MMM YYYY'),
    },
    plan,
    // Run rate to the end of the period. Deliberately null early on, which is
    // the rule #8188 has to settle.
    projected:
      daysElapsed >= 5 ? Math.round((total / daysElapsed) * periodDays) : null,
    restricted,
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
    grace: 'countdown',
    graceDaysLeft: 4,
    isBillingPeriod: false,
    limit: 50_000,
    percent: 112,
    periodDays: 30,
    periodLabel: 'Last 30 days',
    plan: 'free',
  }),
  'free-restricted': buildView({
    daysElapsed: 27,
    grace: 'restricted',
    isBillingPeriod: false,
    limit: 50_000,
    percent: 137,
    periodDays: 30,
    periodLabel: 'Last 30 days',
    plan: 'free',
    restricted: true,
  }),
  healthy: buildView({
    daysElapsed: 17,
    grace: 'available',
    limit: 2_000_000,
    percent: 62,
    periodDays: 30,
    plan: 'paid',
  }),
  'over-charged': buildView({
    daysElapsed: 21,
    grace: 'used',
    limit: 2_000_000,
    overageCost: 1340,
    percent: 128,
    periodDays: 30,
    plan: 'paid',
  }),
  'over-covered': buildView({
    daysElapsed: 19,
    grace: 'covering',
    limit: 2_000_000,
    percent: 118,
    periodDays: 30,
    plan: 'paid',
  }),
}
