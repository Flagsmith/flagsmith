import { FC, useMemo } from 'react'
import { Res } from 'common/types/responses'
import LineChart from 'components/charts/LineChart'
import { ChartDataPoint } from 'components/charts/types'
import './UsageBillingPrototype.scss'

type UsageBillingPrototypeProps = {
  data: Res['organisationUsage'] | undefined
  maxApiCalls?: number | null
}

const ACCENT = '#6837fc'
const DANGER = '#ef4d56'

// Compact number formatting to match the design (1.24M / 68.4k).
const compact = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return `${n}`
}

/**
 * SPIKE — Billing & Usage Transparency prototype.
 * Reframes the usage view as "usage vs plan limit" using ONLY data the
 * frontend already receives (usage-data totals/events + max_api_calls).
 * Everything the API cannot feed yet is marked TODO(BE) and listed in the
 * "needs BE" panel below, so the diff doubles as the backend ask.
 */
const UsageBillingPrototype: FC<UsageBillingPrototypeProps> = ({
  data,
  maxApiCalls,
}) => {
  const total = data?.totals?.total ?? 0
  const limit = maxApiCalls ?? 0
  const pct = limit > 0 ? Math.round((total / limit) * 100) : 0
  const over = pct >= 100

  // Cumulative usage over the period = running sum of the daily event totals.
  const chartData = useMemo<ChartDataPoint[]>(() => {
    const events = [...(data?.events_list ?? [])].sort((a, b) =>
      a.day < b.day ? -1 : 1,
    )
    let running = 0
    return events.map((event) => {
      running +=
        (event.flags ?? 0) +
        (event.identities ?? 0) +
        (event.traits ?? 0) +
        (event.environment_document ?? 0)
      // `limit` is repeated on every point so LineChart draws a flat ceiling.
      return { cumulative: running, day: event.day, limit }
    })
  }, [data?.events_list, limit])

  return (
    <div className='usage-proto mb-4'>
      <div className='usage-proto__head'>
        <h5 className='mb-0'>Usage vs plan limit</h5>
        {/* TODO(BE): billing-period reset date is not serialised. The dates
            exist on OrganisationSubscriptionInformationCache
            (current_billing_term_starts_at/ends_at) but are never exposed on
            usage-data or get-subscription-metadata. */}
        <span className='usage-proto__stub'>Resets: needs BE</span>
      </div>

      <div className='usage-proto__headline'>
        <span
          className='usage-proto__pct'
          style={{ color: over ? DANGER : ACCENT }}
        >
          {pct}%
        </span>
        <span className='usage-proto__sub'>
          of plan consumed · {compact(total)} / {limit ? compact(limit) : '—'}{' '}
          API calls
        </span>
      </div>

      <div className='usage-proto__track'>
        <div
          className='usage-proto__fill'
          // Only the dynamic fill width/colour is inline; the rest is in SCSS.
          style={{
            background: over ? DANGER : ACCENT,
            width: `${Math.min(pct, 100)}%`,
          }}
        />
      </div>

      <LineChart
        data={chartData}
        series={['cumulative', 'limit']}
        colorMap={{ cumulative: ACCENT, limit: DANGER }}
        seriesLabels={{ cumulative: 'Cumulative usage', limit: 'Plan limit' }}
        height={300}
        showLegend
      />

      <div className='usage-proto__notes'>
        <strong>Prototype notes — wired to existing data:</strong> % of plan,
        cumulative chart, and the plan-limit ceiling all come from
        <code> usage-data</code> + <code>max_api_calls</code>, no BE change.
        <div className='mt-2'>
          <strong>Needs BE (see PR description):</strong>
          <ul className='mb-0 mt-1'>
            <li>Reset date / billing-period boundaries (not serialised)</li>
            <li>
              Fix the current-billing-period date-range bug (annual plans)
            </li>
            <li>Projected end-of-period (needs the period length above)</li>
            <li>Grace-period status and cost in currency (not exposed)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default UsageBillingPrototype
