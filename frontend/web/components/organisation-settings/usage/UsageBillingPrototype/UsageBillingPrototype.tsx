import { FC } from 'react'
import ProjectFilter from 'components/ProjectFilter'
import { billingPeriods, freePeriods, Req } from 'common/types/requests'
import UsageBanner from './UsageBanner'
import UsageChart from './UsageChart'
import GraceChip from './GraceChip'
import { UsageView } from './types'
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
  isOnFreePlanPeriods: boolean
}

type Tile = {
  label: string
  value: string
  sub: string
  badge?: { text: string; tone: 'success' | 'warning' | 'danger' | 'estimate' }
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
          : { text: percent >= 75 ? 'Watch' : 'On track', tone: 'success' },
      label: 'Total API calls',
      sub: view.limit
        ? `of ${compact(view.limit)} plan limit`
        : 'no plan limit',
      value: compact(view.total),
    },
    {
      label: '% of plan consumed',
      sub: view.period.isBillingPeriod ? 'this billing period' : 'this period',
      value: view.limit ? `${percent}%` : '—',
    },
    {
      label: 'Days remaining',
      sub: view.period.resetsAt
        ? `resets ${view.period.resetsAt}`
        : 'needs the billing period',
      value: view.period.daysRemaining ? `${view.period.daysRemaining}` : '—',
    },
  ]

  if (view.restricted) {
    tiles.push({
      badge: { text: 'Paused', tone: 'danger' },
      label: 'Flag serving',
      sub: 'resumes on upgrade',
      value: 'Paused',
    })
  } else if (view.overageCost !== null) {
    tiles.push({
      badge: { text: 'Estimate', tone: 'estimate' },
      label: 'Est. overage cost',
      sub: 'charged at the end of the period',
      value: currency(view.overageCost),
    })
  } else {
    tiles.push({
      badge: { text: 'Estimate', tone: 'estimate' },
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
  isOnFreePlanPeriods,
  organisationId,
  project,
  setBillingPeriod,
  setProject,
  view,
}) => {
  const percent = view.limit ? Math.round((view.total / view.limit) * 100) : 0
  const tone = toneForPercent(percent)
  const maxBreakdown = Math.max(1, ...view.breakdown.map((row) => row.value))
  const breakdownTotal = view.breakdown.reduce((acc, row) => acc + row.value, 0)

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
              options={isOnFreePlanPeriods ? freePeriods : billingPeriods}
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
            {view.period.isBillingPeriod ? 'Billing period' : 'Period'}
          </strong>{' '}
          {view.period.label}
        </span>
        <span className='usage-proto__strip-right'>
          <GraceChip grace={view.grace} daysLeft={view.graceDaysLeft} />
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
          <div className='usage-proto__track'>
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
      </div>

      <div className='usage-proto__tiles'>
        {buildTiles(view, percent).map((tile) => (
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
          <strong>Usage by request type</strong>
          <span className='usage-proto__sub'>
            Where your API calls came from
          </span>
        </div>
        <div className='usage-proto__breakdown'>
          {[...view.breakdown]
            .sort((a, b) => b.value - a.value)
            .map((row) => (
              <div className='usage-proto__row' key={row.op}>
                <div className='usage-proto__row-label'>
                  <div>{row.label}</div>
                  <div className='usage-proto__sub'>{row.op}</div>
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
