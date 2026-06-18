import { FC, ReactNode, useMemo } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import Icon from 'components/icons/Icon'
import {
  BayesianMetricResult,
  BayesianResultsSummary,
  ExpectedDirection,
  Experiment,
  Inference,
  MetricAggregation,
} from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import { VariantIdentity, getVariantIdentities } from './derive'
import './results.scss'

type ExperimentMetricScorecardProps = {
  experiment: Experiment
  results?: BayesianResultsSummary
}

const renderMean = (
  mean: number | null,
  aggregation: MetricAggregation,
): string => {
  if (mean === null) return '—'
  if (aggregation === 'occurrence') return `${(mean * 100).toFixed(1)}%`
  return mean.toFixed(2)
}

const isLiftFavourable = (
  lift: number,
  direction: ExpectedDirection,
): boolean => {
  if (direction === 'increase' || direction === 'not_decrease') return lift > 0
  return lift < 0
}

const liftColour = (lift: number, direction: ExpectedDirection): string =>
  isLiftFavourable(lift, direction)
    ? 'var(--color-text-success)'
    : 'var(--color-text-danger)'

type AxisRange = { min: number; max: number }

const computeAxisRange = (
  identities: VariantIdentity[],
  metricResult?: BayesianMetricResult,
): AxisRange => {
  let min = -0.1
  let max = 0.1
  identities.forEach((v) => {
    if (v.isControl) return
    const inf = metricResult?.inference[v.key]
    if (!inf) return
    if (inf.ci_low < min) min = inf.ci_low
    if (inf.ci_high > max) max = inf.ci_high
  })
  const pad = (max - min) * 0.15
  return { max: max + pad, min: min - pad }
}

const valueToPercent = (value: number, range: AxisRange): number =>
  ((value - range.min) / (range.max - range.min)) * 100

const buildTicks = (range: AxisRange): number[] => {
  const span = range.max - range.min
  let step = 0.05
  if (span > 0.6) step = 0.2
  else if (span > 0.3) step = 0.1

  const ticks: number[] = []
  const start = Math.ceil(range.min / step) * step
  for (let v = start; v <= range.max; v += step) {
    ticks.push(Math.round(v * 1000) / 1000)
  }
  return ticks
}

const TickLines: FC<{ ticks: number[]; range: AxisRange }> = ({
  range,
  ticks,
}) => (
  <>
    {ticks.map((t) => (
      <div
        key={t}
        className={`experiment-results__axis-tick-line${
          t === 0 ? ' experiment-results__axis-tick-line--zero' : ''
        }`}
        style={{ left: `${valueToPercent(t, range)}%` }}
      />
    ))}
  </>
)

const SharedAxisChart: FC<{
  identities: VariantIdentity[]
  metricName: string
  metricResult?: BayesianMetricResult
  direction: ExpectedDirection
  range: AxisRange
}> = ({ direction, identities, metricName, metricResult, range }) => {
  const ticks = useMemo(() => buildTicks(range), [range])

  return (
    <div className='experiment-results__axis-card'>
      <div className='experiment-results__axis-metric-header'>
        <span className='selectable-card__badge selectable-card__badge--primary'>
          Primary
        </span>
        <strong>{metricName}</strong>
      </div>
      <div className='experiment-results__axis-chart'>
        <div className='experiment-results__axis-header'>
          {ticks.map((t) => (
            <span
              key={t}
              className='experiment-results__axis-tick-label'
              style={{ left: `${valueToPercent(t, range)}%` }}
            >
              {t === 0 ? '0%' : `${(t * 100).toFixed(0)}%`}
            </span>
          ))}
        </div>
        <div className='experiment-results__axis-tracks'>
          <div className='experiment-results__axis-grid'>
            <TickLines range={range} ticks={ticks} />
          </div>
          {identities.map((v) => {
            const inf = metricResult?.inference[v.key] ?? null
            if (v.isControl) {
              return (
                <div key={v.key} className='experiment-results__axis-row'>
                  <div className='experiment-results__axis-track'>
                    <span
                      className='experiment-results__axis-row-label'
                      style={{
                        left: `${valueToPercent(0, range)}%`,
                        transform: 'translate(-50%, -50%)',
                      }}
                    >
                      <ColorSwatch color={v.colour} shape='circle' size='sm' />
                      {v.name}
                    </span>
                  </div>
                </div>
              )
            }
            if (!inf) return null
            const colour = liftColour(inf.lift, direction)
            const ciLeft = valueToPercent(inf.ci_low, range)
            const ciRight = valueToPercent(inf.ci_high, range)
            const dotPos = valueToPercent(inf.lift, range)
            return (
              <div key={v.key} className='experiment-results__axis-row'>
                <div className='experiment-results__axis-track'>
                  <span
                    className='experiment-results__axis-row-label'
                    style={{ left: `${ciLeft}%` }}
                  >
                    <ColorSwatch color={v.colour} shape='circle' size='sm' />
                    {v.name}
                  </span>
                  <div
                    className='experiment-results__axis-bar'
                    style={{
                      background: colour,
                      left: `${ciLeft}%`,
                      width: `${ciRight - ciLeft}%`,
                    }}
                  />
                  <div
                    className='experiment-results__axis-dot'
                    style={{ background: colour, left: `${dotPos}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

const LIFT_RANGE = 0.3
const liftToPercent = (value: number): number =>
  Math.max(0, Math.min(100, ((value / LIFT_RANGE + 1) / 2) * 100))

const renderLift = (
  identity: VariantIdentity,
  inference: Inference | null,
  direction: ExpectedDirection,
): ReactNode => {
  if (identity.isControl) {
    return <span className='text-muted fs-caption'>Baseline</span>
  }
  if (!inference) {
    return <span className='text-muted fs-caption'>Collecting data…</span>
  }
  const liftPct = inference.lift * 100
  const colour = liftColour(inference.lift, direction)
  const left = liftToPercent(inference.ci_low)
  const right = liftToPercent(inference.ci_high)
  const dotPos = liftToPercent(inference.lift)

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
        {liftPct >= 0 ? '+' : ''}
        {liftPct.toFixed(1)}%
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
  const colour = isHighest
    ? 'var(--color-text-success)'
    : 'var(--color-text-secondary)'
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

const ExperimentMetricScorecard: FC<ExperimentMetricScorecardProps> = ({
  experiment,
  results,
}) => {
  const metric = getPrimaryMetric(experiment)
  const identities = getVariantIdentities(experiment.feature)
  const metricResult = metric
    ? results?.metrics.find((m) => m.metric_id === metric.metric)
    : undefined
  const srmBroken =
    !!results && results.srm_p_value !== null && results.srm_p_value < 0.001

  const highestCtw = identities.reduce<{
    key: string | null
    value: number
  }>(
    (best, v) => {
      if (v.isControl) return best
      const ctw = metricResult?.inference[v.key]?.chance_to_win ?? 0
      return ctw > best.value ? { key: v.key, value: ctw } : best
    },
    { key: null, value: 0 },
  )

  const axisRange = useMemo(
    () => computeAxisRange(identities, metricResult),
    [identities, metricResult],
  )

  if (!metric) return null

  return (
    <>
      {metricResult && (
        <SharedAxisChart
          direction={metric.expected_direction}
          identities={identities}
          metricName={metric.metric_name}
          metricResult={metricResult}
          range={axisRange}
        />
      )}

      <div className='experiment-results__scorecard mb-4'>
        {srmBroken && (
          <div className='alert alert-danger m-3 mb-0'>
            Sample ratio mismatch detected — the variation split looks broken;
            interpret results with caution.
          </div>
        )}

        <table className='experiment-results__scorecard-table'>
          <thead>
            <tr>
              <th style={{ width: '10%' }}>Variant</th>
              <th style={{ width: '8%' }}>Exposures</th>
              <th style={{ width: '12%' }}>
                {metric.aggregation === 'occurrence'
                  ? 'Occurrence Rate'
                  : 'Mean'}
              </th>
              <th style={{ width: '24%' }}>
                <Tooltip
                  title={
                    <span className='d-inline-flex align-items-center gap-1'>
                      Delta
                      <Icon name='info-outlined' width={16} fill='#9DA4AE' />
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
                    <span className='d-inline-flex align-items-center gap-1'>
                      Credible Interval (95%)
                      <Icon name='info-outlined' width={16} fill='#9DA4AE' />
                    </span>
                  }
                >
                  The range we are 95% confident the true lift falls within. If
                  it doesn't cross zero, the result is statistically
                  significant.
                </Tooltip>
              </th>
              <th style={{ width: '16%' }}>Win Probability</th>
            </tr>
          </thead>
          <tbody>
            {identities.map((v) => {
              const stats = metricResult?.variants[v.key]
              const inference = metricResult?.inference[v.key] ?? null
              const mean = stats && stats.n > 0 ? stats.sum / stats.n : null
              return (
                <tr key={v.key}>
                  <td>
                    <span className='d-flex align-items-center gap-2'>
                      <ColorSwatch color={v.colour} shape='circle' size='sm' />
                      {v.name}
                    </span>
                  </td>
                  <td>{stats ? stats.n.toLocaleString() : '—'}</td>
                  <td>{renderMean(mean, metric.aggregation)}</td>
                  <td>{renderLift(v, inference, metric.expected_direction)}</td>
                  <td>{renderCI(v, inference)}</td>
                  <td>
                    {renderWinProbability(
                      v,
                      inference,
                      v.key === highestCtw.key,
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}

export default ExperimentMetricScorecard
