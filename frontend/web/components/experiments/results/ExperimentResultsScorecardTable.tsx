import { FC, ReactNode } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'
import {
  colorIconSecondary,
  colorTextDanger,
  colorTextSecondary,
  colorTextSuccess,
} from 'common/theme/tokens'
import {
  BayesianMetricResult,
  ExpectedDirection,
  ExperimentMetric,
  Inference,
  MetricAggregation,
  VariantStats,
} from 'common/types/responses'
import {
  VariantIdentity,
  formatLiftPct,
  isLiftFavourable,
  liftToPercent,
} from './derive'

const AGGREGATION_HEADER: Record<MetricAggregation, string> = {
  count: 'Count',
  mean: 'Mean',
  occurrence: 'Occ. Rate',
  sum: 'Sum',
}

const renderMetricValue = (
  stats: Pick<VariantStats, 'n' | 'sum'> | undefined,
  aggregation: MetricAggregation,
): string => {
  if (!stats || stats.n === 0) return '—'
  if (aggregation === 'count' || aggregation === 'sum')
    return stats.sum.toLocaleString(undefined, { maximumFractionDigits: 2 })
  const mean = stats.sum / stats.n
  if (aggregation === 'occurrence') return `${(mean * 100).toFixed(1)}%`
  return mean.toFixed(2)
}

const getLiftColour = (lift: number, direction: ExpectedDirection): string =>
  isLiftFavourable(lift, direction) ? colorTextSuccess : colorTextDanger

const renderLift = (
  identity: VariantIdentity,
  inference: Inference | null,
  direction: ExpectedDirection,
  liftRange: number,
): ReactNode => {
  if (identity.isControl) {
    return <span className='text-muted fs-caption'>Baseline</span>
  }
  if (!inference) {
    return <span className='text-muted fs-caption'>Collecting data…</span>
  }
  const colour = getLiftColour(inference.lift, direction)
  const left = liftToPercent(inference.ci_low, liftRange)
  const right = liftToPercent(inference.ci_high, liftRange)
  const dotPos = liftToPercent(inference.lift, liftRange)

  return (
    <div className='experiment-results__lift-bar'>
      <div className='experiment-results__lift-track'>
        <div className='experiment-results__lift-zero' />
        <div
          className='experiment-results__lift-fill'
          style={{
            background: colour,
            left: `${left}%`,
            width: `${right - left}%`,
          }}
        />
        <div
          className='experiment-results__lift-dot'
          style={{ background: colour, left: `${dotPos}%` }}
        />
      </div>
      <span
        className='experiment-results__lift-value'
        style={{ color: colour }}
      >
        {formatLiftPct(inference.lift)}
      </span>
    </div>
  )
}

const renderCI = (
  identity: VariantIdentity,
  inference: Inference | null,
): ReactNode => {
  if (identity.isControl) {
    return <span className='text-muted fs-caption'>Baseline</span>
  }
  if (!inference) return '—'
  return (
    <span className='fs-caption'>
      [{(inference.ci_low * 100).toFixed(1)}%,{' '}
      {(inference.ci_high * 100).toFixed(1)}%]
    </span>
  )
}

const renderWinProbability = (
  identity: VariantIdentity,
  inference: Inference | null,
  isHighest: boolean,
): ReactNode => {
  if (identity.isControl || !inference) return '—'
  const pct = Math.round(inference.chance_to_win * 100)
  const colour = isHighest ? colorTextSuccess : colorTextSecondary
  return (
    <div className='experiment-results__win-prob'>
      <div className='experiment-results__win-prob-track'>
        <div
          className='experiment-results__win-prob-fill'
          style={{ background: colour, width: `${pct}%` }}
        />
      </div>
      <span style={{ color: colour }}>{pct}%</span>
    </div>
  )
}

type ExperimentResultsScorecardTableProps = {
  identities: VariantIdentity[]
  liftRange: number
  metric: ExperimentMetric
  metricResult?: BayesianMetricResult
  srmBroken: boolean
  winnerKey?: string
}

const ExperimentResultsScorecardTable: FC<
  ExperimentResultsScorecardTableProps
> = ({ identities, liftRange, metric, metricResult, srmBroken, winnerKey }) => (
  <div className='mb-4'>
    <div className='experiment-results__scorecard'>
      <table className='experiment-results__scorecard-table'>
        <thead>
          <tr>
            <th style={{ width: '10%' }}>Variant</th>
            <th style={{ width: '8%' }}>Exposures</th>
            <th style={{ width: '12%' }}>
              {AGGREGATION_HEADER[metric.aggregation]}
            </th>
            <th style={{ width: '24%' }}>
              <Tooltip
                title={
                  <span className='d-inline-flex align-items-center gap-1 flex-nowrap'>
                    Delta
                    <Icon
                      className='flex-shrink-0'
                      name='info-outlined'
                      width={16}
                      fill={colorIconSecondary}
                    />
                  </span>
                }
              >
                How much better or worse a variant performed compared to
                control, as a percentage of the control's value.
              </Tooltip>
            </th>
            <th style={{ width: '16%' }}>
              <Tooltip
                title={
                  <span className='d-inline-flex align-items-center gap-1 flex-nowrap'>
                    Credible Interval (95%)
                    <Icon
                      className='flex-shrink-0'
                      name='info-outlined'
                      width={16}
                      fill={colorIconSecondary}
                    />
                  </span>
                }
              >
                The range we are 95% confident the true lift falls within. If it
                doesn't cross zero, the result is statistically significant.
              </Tooltip>
            </th>
            <th style={{ width: '16%' }}>Win Probability</th>
          </tr>
        </thead>
        <tbody>
          {identities.map((v) => {
            const stats = metricResult?.variants[v.key]
            const inference = metricResult?.inference[v.key] ?? null
            return (
              <tr key={v.key}>
                <td>
                  <span className='d-flex align-items-center gap-2'>
                    <ColorSwatch color={v.colour} shape='circle' size='sm' />
                    {v.name}
                  </span>
                </td>
                <td>{stats ? stats.n.toLocaleString() : '—'}</td>
                <td>{renderMetricValue(stats, metric.aggregation)}</td>
                <td>
                  {renderLift(
                    v,
                    inference,
                    metric.expected_direction,
                    liftRange,
                  )}
                </td>
                <td>{renderCI(v, inference)}</td>
                <td>
                  {renderWinProbability(v, inference, v.key === winnerKey)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
    {srmBroken && (
      <p className='text-danger fst-italic fs-caption mt-1 mb-0'>
        Sample ratio mismatch detected — the variation split looks broken;
        interpret results with caution.
      </p>
    )}
  </div>
)

export default ExperimentResultsScorecardTable
