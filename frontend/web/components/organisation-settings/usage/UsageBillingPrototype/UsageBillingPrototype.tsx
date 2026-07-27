import { FC, useMemo } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Res } from 'common/types/responses'
import { colorTextSecondary } from 'common/theme/tokens'
import './UsageBillingPrototype.scss'

type UsageBillingPrototypeProps = {
  data: Res['organisationUsage'] | undefined
  maxApiCalls?: number | null
}

const ACCENT = '#6837fc'
const DANGER = '#ef4d56'
const SUCCESS = '#27ab95'
const WARNING = '#f79009'

// Compact number formatting to match the design (1.24M / 68.4k).
const compact = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return `${Math.round(n)}`
}

// Green under 75%, amber approaching, red at/over the limit.
const meterColorFor = (percent: number): string => {
  if (percent >= 100) return DANGER
  if (percent >= 75) return WARNING
  return SUCCESS
}

type Tile = {
  label: string
  value: string
  sub: string
  badge?: { text: string; tone: 'success' | 'estimate' }
}

/**
 * SPIKE — Billing & Usage Transparency prototype (S1 / healthy).
 * Builds the v0.2 Pencil design against ONLY data the frontend already
 * receives (usage-data totals/events + max_api_calls). Anything the API
 * cannot feed yet is marked TODO(BE) and surfaced in the notes panel, so the
 * diff doubles as the backend ask.
 */
const UsageBillingPrototype: FC<UsageBillingPrototypeProps> = ({
  data,
  maxApiCalls,
}) => {
  const total = data?.totals?.total ?? 0
  const limit = maxApiCalls ?? 0
  const pct = limit > 0 ? Math.round((total / limit) * 100) : 0
  const over = pct >= 100
  const meterColor = meterColorFor(pct)

  // Cumulative usage over the period = running sum of the daily event totals.
  const { chartData, todayPoint } = useMemo(() => {
    const events = [...(data?.events_list ?? [])].sort((a, b) =>
      a.day < b.day ? -1 : 1,
    )
    let running = 0
    const points = events.map((event) => {
      running +=
        (event.flags ?? 0) +
        (event.identities ?? 0) +
        (event.traits ?? 0) +
        (event.environment_document ?? 0)
      return { cumulative: running, day: event.day }
    })
    return {
      chartData: points,
      todayPoint: points[points.length - 1],
    }
  }, [data?.events_list])

  // Request-type breakdown (the four billable types), ranked by volume.
  const breakdown = useMemo(() => {
    const t = data?.totals
    const rows = [
      { label: 'Flag evaluations', op: 'get-flags', value: t?.flags ?? 0 },
      {
        label: 'Identity flag evaluations',
        op: 'get-identity-flags',
        value: t?.identities ?? 0,
      },
      {
        label: 'Trait updates',
        op: 'set-identity-traits',
        value: t?.traits ?? 0,
      },
      {
        label: 'Environment bootstrap',
        op: 'get-environment-document',
        value: t?.environmentDocument ?? 0,
      },
    ]
    const max = Math.max(1, ...rows.map((r) => r.value))
    return rows
      .sort((a, b) => b.value - a.value)
      .map((r) => ({ ...r, width: Math.round((r.value / max) * 100) }))
  }, [data?.totals])

  const tiles: Tile[] = [
    {
      badge: over
        ? undefined
        : { text: pct >= 75 ? 'Watch' : 'On track', tone: 'success' },
      label: 'Total API calls',
      sub: `of ${limit ? compact(limit) : '—'} plan limit`,
      value: compact(total),
    },
    {
      label: '% of plan consumed',
      sub: 'this period', // TODO(BE): days-left needs the reset date
      value: `${pct}%`,
    },
    {
      // TODO(BE): projection needs the billing-period length (reset date)
      badge: { text: 'Estimate', tone: 'estimate' },
      label: 'Projected end-of-period',
      sub: 'needs period length (BE)',
      value: '—',
    },
    {
      // TODO(BE): no per-org pricing is exposed; Chargebee only
      badge: { text: 'Estimate', tone: 'estimate' },
      label: 'Est. cost this period',
      sub: 'needs pricing (BE)',
      value: '—',
    },
  ]

  return (
    <div className='usage-proto mb-4'>
      {/* Billing-period strip */}
      <div className='usage-proto__strip'>
        <span>
          <strong>Billing period</strong>{' '}
          <span className='usage-proto__stub'>needs BE (boundaries)</span>
        </span>
        {/* TODO(BE): reset date not serialised (OrganisationSubscription
            InformationCache.current_billing_term_ends_at) */}
        <span className='usage-proto__stub'>Resets: needs BE</span>
      </div>

      {/* Hero meter */}
      <div className='usage-proto__panel'>
        <div className='usage-proto__headline'>
          <div>
            <div className='usage-proto__label'>Plan usage this period</div>
            <div className='usage-proto__big'>
              <span className='usage-proto__pct' style={{ color: meterColor }}>
                {pct}%
              </span>
              <span className='usage-proto__sub'>of plan consumed</span>
            </div>
          </div>
          <div className='usage-proto__frac'>
            <div>
              <strong>{compact(total)}</strong> / {limit ? compact(limit) : '—'}
            </div>
            <div className='usage-proto__sub'>API calls used / plan limit</div>
          </div>
        </div>

        <div className='usage-proto__meter'>
          <div className='usage-proto__track'>
            <div
              className='usage-proto__fill'
              style={{
                background: meterColor,
                width: `${Math.min(pct, 100)}%`,
              }}
            />
          </div>
          <span className='usage-proto__marker' style={{ left: '75%' }}>
            <span
              className='usage-proto__marker-label'
              style={{ color: WARNING }}
            >
              Notify 75%
            </span>
          </span>
          <span className='usage-proto__marker' style={{ left: '100%' }}>
            <span
              className='usage-proto__marker-label'
              style={{ color: DANGER }}
            >
              Notify 100%
            </span>
          </span>
        </div>
      </div>

      {/* Stat tiles */}
      <div className='usage-proto__tiles'>
        {tiles.map((tile) => (
          <div className='usage-proto__tile' key={tile.label}>
            <div className='usage-proto__tile-head'>
              <span className='usage-proto__tile-label'>{tile.label}</span>
              {tile.badge && (
                <span
                  className={`usage-proto__badge usage-proto__badge--${tile.badge.tone}`}
                >
                  {tile.badge.text}
                </span>
              )}
            </div>
            <div className='usage-proto__tile-value'>{tile.value}</div>
            <div className='usage-proto__sub'>{tile.sub}</div>
          </div>
        ))}
      </div>

      {/* Cumulative usage vs plan limit */}
      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <strong>Usage vs plan limit</strong>
          <span className='usage-proto__sub'>Cumulative · this period</span>
        </div>
        <ResponsiveContainer height={320} width='100%'>
          <ComposedChart
            data={chartData}
            margin={{ bottom: 0, left: 0, right: 16, top: 8 }}
          >
            <defs>
              <linearGradient id='usageProtoArea' x1='0' x2='0' y1='0' y2='1'>
                <stop offset='0%' stopColor={ACCENT} stopOpacity={0.18} />
                <stop offset='100%' stopColor={ACCENT} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray='3 5'
              strokeOpacity={0.4}
              vertical={false}
            />
            <XAxis
              dataKey='day'
              height={70}
              angle={-90}
              textAnchor='end'
              interval={Math.ceil((chartData.length || 1) / 12)}
              tick={{ dx: -4, fill: colorTextSecondary, fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: colorTextSecondary }}
            />
            <YAxis
              tick={{ fill: colorTextSecondary, fontSize: 11 }}
              axisLine={{ stroke: colorTextSecondary }}
              tickFormatter={(value) =>
                value >= 1000 ? `${(value / 1000).toFixed(0)}k` : `${value}`
              }
            />
            <Tooltip
              formatter={(value: number) => [compact(value), 'Cumulative']}
            />
            <Area
              type='monotone'
              dataKey='cumulative'
              stroke={ACCENT}
              strokeWidth={2.5}
              fill='url(#usageProtoArea)'
              dot={false}
              isAnimationActive={false}
            />
            {limit > 0 && (
              <ReferenceLine
                y={limit}
                stroke={DANGER}
                strokeWidth={2}
                label={{
                  fill: DANGER,
                  fontSize: 11,
                  position: 'insideTopRight',
                  value: `Plan limit · ${compact(limit)}`,
                }}
              />
            )}
            {todayPoint && (
              <ReferenceDot
                r={4}
                fill={ACCENT}
                stroke='#fff'
                strokeWidth={2}
                x={todayPoint.day}
                y={todayPoint.cumulative}
                isFront
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Usage by request type */}
      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <strong>Usage by request type</strong>
          <span className='usage-proto__sub'>
            Where your API calls came from
          </span>
        </div>
        <div className='usage-proto__breakdown'>
          {breakdown.map((row, i) => (
            <div className='usage-proto__row' key={row.op}>
              <div className='usage-proto__row-label'>
                <div>{row.label}</div>
                <div className='usage-proto__sub'>{row.op}</div>
              </div>
              <div className='usage-proto__bar-track'>
                <div
                  className='usage-proto__bar-fill'
                  style={{
                    background:
                      [ACCENT, '#8b5cf6', '#a78bfa', '#c4b5fd'][i] ?? ACCENT,
                    width: `${row.width}%`,
                  }}
                />
              </div>
              <div className='usage-proto__row-value'>{compact(row.value)}</div>
              <div className='usage-proto__sub usage-proto__row-pct'>
                {total ? Math.round((row.value / total) * 100) : 0}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prototype notes / BE gaps */}
      <div className='usage-proto__notes'>
        <strong>Prototype notes — wired to existing data:</strong> % of plan,
        the cumulative chart + ceiling, and the request-type breakdown all come
        from <code>usage-data</code> + <code>max_api_calls</code>, no BE change.
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
