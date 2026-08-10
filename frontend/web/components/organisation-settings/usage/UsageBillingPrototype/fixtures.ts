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
  | 'free-healthy'
  | 'free-approaching'
  | 'free-countdown'
  | 'free-countdown-dated'
  | 'free-grace-exhausted'
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
  { id: 'free-healthy', label: 'Free, healthy' },
  { id: 'free-approaching', label: 'Free, approaching limit' },
  { id: 'free-countdown', label: 'Free, over limit (grace intact)' },
  {
    id: 'free-countdown-dated',
    label: 'Free, grace countdown (needs API support)',
  },
  { id: 'free-grace-exhausted', label: 'Free, over limit (grace used)' },
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
  // Free limits are enforced over a trailing 30 days, so there is no period
  // start to count from and no end to project to. Paid resets with the billing
  // term. Cancelled subscriptions roll like free, which this fixture set does
  // not cover yet.
  const rolling = plan === 'free'
  const windowStart = moment().subtract(periodDays - 1, 'days')

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
    period: rolling
      ? {
          // Nothing to count down to: the window moves forward every day.
          daysRemaining: 0,
          isBillingPeriod: false,
          label: `${windowStart.format('D MMM')} to ${moment().format(
            'D MMM YYYY',
          )}`,
          // Rolling windows never reset, so they get no reset date.
          resetsAt: '',
          selectValue: undefined,
        }
      : {
          daysRemaining: periodDays - daysElapsed,
          isBillingPeriod: true,
          label: `${periodStart.format('D MMM')} to ${resetsAt.format(
            'D MMM YYYY',
          )}`,
          resetsAt: resetsAt.format('D MMM YYYY'),
          selectValue: 'current_billing_period',
        },

    plan,
    // Run rate to the end of the period. Deliberately null early on, which is
    // the rule #8188 has to settle. A rolling window has no end to run to, and
    // projecting a total that can fall is the part that misleads, so it stays
    // null there.
    projected:
      !rolling && daysElapsed >= 5
        ? Math.round((total / daysElapsed) * periodDays)
        : null,
    restricted,
    restrictedImmediately,
    resumesAt,
    series: rolling
      ? buildSeries(total, periodDays, windowStart)
      : buildSeries(total, daysElapsed, periodStart),
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
  // The two states most free orgs are actually in. A trailing window is always
  // full, so daysElapsed matches the window length.
  'free-approaching': buildView({
    daysElapsed: 30,
    grace: 'available',
    limit: 50_000,
    percent: 78,
    periodDays: 30,
    plan: 'free',
  }),
  // Today's truth: we know they are over and that grace is intact, but not how
  // long is left, because the notification date is not exposed.
  'free-countdown': buildView({
    daysElapsed: 22,
    daysOverLimit: 4,
    grace: 'countdown',
    limit: 50_000,
    percent: 112,
    periodDays: 30,
    plan: 'free',
  }),
  // The same state once the API can answer "how long". Kept separate so the
  // gap between what we can say now and what we want to say is visible.
  'free-countdown-dated': buildView({
    daysElapsed: 22,
    daysOverLimit: 4,
    grace: 'countdown',
    graceDaysLeft: 3,
    limit: 50_000,
    percent: 112,
    periodDays: 30,
    plan: 'free',
  }),
  // Over the limit with grace already spent. No countdown exists for this org;
  // the next task run can cut them off.
  'free-grace-exhausted': buildView({
    daysElapsed: 25,
    daysOverLimit: 2,
    grace: 'exhausted',
    limit: 50_000,
    percent: 108,
    periodDays: 30,
    plan: 'free',
  }),
  'free-healthy': buildView({
    daysElapsed: 30,
    grace: 'available',
    limit: 50_000,
    percent: 62,
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
    // No resumesAt: a trailing window never resets, so there is no date to
    // promise. The tile carries the condition instead.
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
