import { FC, useMemo } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import { BayesianMetricResult } from 'common/types/responses'
import {
  AxisRange,
  VariantIdentity,
  buildTicks,
  formatLiftPct,
  getLiftColour,
  valueToPercent,
} from './derive'

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

type ExperimentResultsAxisChartProps = {
  identities: VariantIdentity[]
  metricName: string
  metricResult?: BayesianMetricResult
  range: AxisRange
}

const ExperimentResultsAxisChart: FC<ExperimentResultsAxisChartProps> = ({
  identities,
  metricName,
  metricResult,
  range,
}) => {
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
            const colour = getLiftColour(inf.lift)
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
                  <span
                    className='experiment-results__axis-dot-label'
                    style={{ color: colour, left: `${dotPos}%` }}
                  >
                    {formatLiftPct(inf.lift)}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ExperimentResultsAxisChart
