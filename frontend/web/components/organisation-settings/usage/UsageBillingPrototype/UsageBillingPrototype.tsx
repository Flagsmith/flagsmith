import { FC, useState } from 'react'
import ProjectFilter from 'components/ProjectFilter'
import StatItem from 'components/StatItem'
import { billingPeriods, Req } from 'common/types/requests'

// Every widget below the selector assumes a billing period, and free plans now
// have one too, so rolling windows are not offered to anybody.
const billingPeriodOptions = billingPeriods.filter((period) =>
  `${period.value}`.includes('billing_period'),
)
import UsageBanner from './UsageBanner'
import UsageChart from './UsageChart'
import GraceChip from './GraceChip'
import UsageNote from './UsageNote'
import UsageBadge, { BadgeTone } from './UsageBadge'
import { BREAKDOWN_DIMENSIONS, BreakdownDimension, UsageView } from './types'
import { compact, currency } from './format'
import './UsageBillingPrototype.scss'

type UsageBillingPrototypeProps = {
  view: UsageView
  organisationId: number
  project: string | undefined
  setProject: (project: string | undefined) => void
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  setBillingPeriod: (
    period: Req['getOrganisationUsage']['billing_period'],
  ) => void
}

type Tile = {
  label: string
  value: string
  sub: string
  badge?: { text: string; tone: BadgeTone; withDot?: boolean }
}

const toneForPercent = (percent: number): 'success' | 'warning' | 'danger' => {
  if (percent >= 100) return 'danger'
  if (percent >= 75) return 'warning'
  return 'success'
}

const buildTiles = (view: UsageView, percent: number): Tile[] => {
  const tiles: Tile[] = [
    {
      badge:
        percent >= 100
          ? { text: 'Over limit', tone: 'danger' }
          : {
              text: percent >= 75 ? 'Watch' : 'On track',
              tone: percent >= 75 ? 'warning' : 'success',
            },
      label: 'Total API calls',
      sub: view.limit
        ? `of ${compact(view.limit)} plan limit`
        : 'no plan limit',
      value: compact(view.total),
    },
    {
      label: '% of plan consumed',
      sub: view.period.isBillingPeriod ? 'this billing period' : 'this window',
      value: view.limit ? `${percent}%` : '—',
    },
  ]

  // Over the limit, the useful count is how long it has been true, not what is
  // left of a period. On a rolling window there is no end to count down to at
  // all, so the tile is dropped rather than invented.
  if (view.daysOverLimit) {
    tiles.push({
      badge: { text: `${view.daysOverLimit} days`, tone: 'danger' },
      label: 'Days over limit',
      sub: view.overLimitSince ? `since ${view.overLimitSince}` : '',
      value: `${view.daysOverLimit}`,
    })
  } else if (view.period.isBillingPeriod && view.period.daysRemaining) {
    tiles.push({
      label: 'Days remaining',
      sub: `resets ${view.period.resetsAt}`,
      value: `${view.period.daysRemaining}`,
    })
  }

  if (view.restricted) {
    tiles.push({
      badge: { text: 'Paused', tone: 'danger' },
      label: 'Flag serving',
      sub: 'resumes on upgrade',
      value: 'Paused',
    })
  } else if (view.overageCost !== null) {
    tiles.push({
      badge: { text: 'Estimate', tone: 'neutral', withDot: false },
      label: 'Est. overage cost',
      sub: 'charged at the end of the period',
      value: currency(view.overageCost),
    })
  } else {
    tiles.push({
      badge: { text: 'Estimate', tone: 'neutral', withDot: false },
      label: 'Projected end-of-period',
      sub: view.projected ? 'at the current run rate' : 'too early to project',
      value: view.projected ? compact(view.projected) : '—',
    })
  }

  return tiles
}

/**
 * PROTOTYPE (#8184). The billing-aligned usage page, rendered from a view
 * model that is either live data or a fixture. See `usePrototypeUsage`.
 */
const UsageBillingPrototype: FC<UsageBillingPrototypeProps> = ({
  billingPeriod,
  organisationId,
  project,
  setBillingPeriod,
  setProject,
  view,
}) => {
  const [dimension, setDimension] = useState<BreakdownDimension>('request-type')

  const percent = view.limit ? Math.round((view.total / view.limit) * 100) : 0
  const tone = toneForPercent(percent)
  const rows = view.breakdowns[dimension]
  const maxBreakdown = Math.max(1, ...rows.map((row) => row.value))
  const breakdownTotal = rows.reduce((acc, row) => acc + row.value, 0)

  return (
    <div className='usage-proto mb-4'>
      <UsageBanner view={view} />

      <div className='usage-proto__header'>
        <h4 className='usage-proto__title'>Usage</h4>
        <div className='usage-proto__header-filters'>
          <div className='usage-proto__select'>
            <Select
              onChange={(v: any) => setBillingPeriod(v.value)}
              value={billingPeriods.find((v) => v.value === billingPeriod)}
              options={billingPeriodOptions}
            />
          </div>
          <div className='usage-proto__select'>
            <ProjectFilter
              showAll
              organisationId={organisationId}
              onChange={setProject}
              value={project}
            />
          </div>
        </div>
      </div>

      <div className='usage-proto__strip'>
        <span>
          <strong>
            {view.period.isBillingPeriod ? 'Billing period' : 'Usage window'}
          </strong>{' '}
          {view.period.label}
        </span>
        <span className='usage-proto__strip-right'>
          <span className='usage-proto__sub'>
            {view.period.isBillingPeriod ? 'Billing period' : 'Rolling window'}
          </span>
          <GraceChip grace={view.grace} />
          {view.period.resetsAt && <span>Resets {view.period.resetsAt}</span>}
        </span>
      </div>

      <div className='usage-proto__panel'>
        <div className='usage-proto__headline'>
          <div>
            <div className='usage-proto__label'>Plan usage this period</div>
            <div className='usage-proto__big'>
              <span className={`usage-proto__pct usage-proto__pct--${tone}`}>
                {view.limit ? `${percent}%` : compact(view.total)}
              </span>
              <span className='usage-proto__sub'>
                {view.limit ? 'of plan consumed' : 'API calls'}
              </span>
            </div>
          </div>
          <div className='usage-proto__frac'>
            <div>
              <strong>{compact(view.total)}</strong> /{' '}
              {view.limit ? compact(view.limit) : '—'}
            </div>
            <div className='usage-proto__sub'>API calls used / plan limit</div>
          </div>
        </div>

        <div className='usage-proto__meter'>
          <div
            className='usage-proto__track'
            role='progressbar'
            aria-label='Plan usage this period'
            aria-valuenow={percent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuetext={`${percent}% of plan consumed`}
          >
            <div
              className={`usage-proto__fill usage-proto__fill--${tone}`}
              style={{ width: `${Math.min(percent, 100)}%` }}
            />
          </div>
          {view.notifications
            .filter((notification) => notification.enabled)
            .map((notification) => (
              <span
                key={notification.percent}
                className={
                  notification.percent >= 100
                    ? 'usage-proto__marker usage-proto__marker--end'
                    : 'usage-proto__marker'
                }
                style={{ left: `${Math.min(notification.percent, 100)}%` }}
              >
                <span
                  className={`usage-proto__marker-label usage-proto__marker-label--${
                    notification.percent >= 100 ? 'danger' : 'warning'
                  }`}
                >
                  Notify {notification.percent}%
                </span>
              </span>
            ))}
        </div>

        <UsageNote view={view} percent={percent} />
      </div>

      <div className='usage-proto__tiles'>
        {buildTiles(view, percent).map((tile) => (
          <StatItem
            key={tile.label}
            label={tile.label}
            value={tile.value}
            sub={tile.sub}
            badge={
              tile.badge && (
                <UsageBadge tone={tile.badge.tone} withDot={tile.badge.withDot}>
                  {tile.badge.text}
                </UsageBadge>
              )
            }
          />
        ))}
      </div>

      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <strong>Usage vs plan limit</strong>
          <span className='usage-proto__sub'>Cumulative · this period</span>
        </div>
        <UsageChart
          series={view.series}
          limit={view.limit}
          projected={view.projected}
          daysRemaining={view.period.daysRemaining}
        />
      </div>

      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <div>
            <strong>
              {BREAKDOWN_DIMENSIONS.find((d) => d.value === dimension)?.label}
            </strong>
            <div className='usage-proto__sub'>
              Where your API calls came from this period
            </div>
          </div>
          <div className='usage-proto__dimension'>
            <Select
              onChange={(v: any) => setDimension(v.value)}
              value={BREAKDOWN_DIMENSIONS.find((d) => d.value === dimension)}
              options={BREAKDOWN_DIMENSIONS}
            />
          </div>
        </div>
        <div className='usage-proto__breakdown'>
          {!rows.length && (
            <div className='usage-proto__sub'>
              The API does not break usage down this way yet.
            </div>
          )}
          {[...rows]
            .sort((a, b) => b.value - a.value)
            .map((row) => (
              <div className='usage-proto__row' key={row.label}>
                <div className='usage-proto__row-label'>
                  <div>{row.label}</div>
                  {row.op && <div className='usage-proto__sub'>{row.op}</div>}
                </div>
                <div className='usage-proto__bar-track'>
                  <div
                    className='usage-proto__bar-fill'
                    style={{
                      width: `${Math.round((row.value / maxBreakdown) * 100)}%`,
                    }}
                  />
                </div>
                <div className='usage-proto__row-value'>
                  {compact(row.value)}
                </div>
                <div className='usage-proto__sub usage-proto__row-pct'>
                  {breakdownTotal
                    ? Math.round((row.value / breakdownTotal) * 100)
                    : 0}
                  %
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}

export default UsageBillingPrototype
