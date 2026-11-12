import { FC } from 'react'
import './MetricsComparisonTable.scss'

type MetricType = 'primary' | 'secondary'

type LiftDirection = 'positive' | 'negative' | 'neutral'

export type MetricComparison = {
  name: string
  type: MetricType
  control: string
  variant: string
  liftValue: number
  liftDirection: LiftDirection
  significance: string
  isSignificant: boolean
}

type MetricsComparisonTableProps = {
  metrics: MetricComparison[]
}

const MetricsComparisonTable: FC<MetricsComparisonTableProps> = ({
  metrics,
}) => {
  return (
    <div className='metrics-comparison-table'>
      <div className='metrics-comparison-table__head'>
        <span className='metrics-comparison-table__th metrics-comparison-table__th--metric'>
          Metric
        </span>
        <span className='metrics-comparison-table__th metrics-comparison-table__th--value'>
          Control
        </span>
        <span className='metrics-comparison-table__th metrics-comparison-table__th--value'>
          Variant B
        </span>
        <span className='metrics-comparison-table__th metrics-comparison-table__th--lift'>
          Lift
        </span>
        <span className='metrics-comparison-table__th metrics-comparison-table__th--significance'>
          Significance
        </span>
      </div>
      {metrics.map((metric) => {
        const liftPercent = Math.min(Math.abs(metric.liftValue) * 2, 50)
        return (
          <div
            key={metric.name}
            className={`metrics-comparison-table__row${
              metric.type === 'primary'
                ? ' metrics-comparison-table__row--primary'
                : ''
            }`}
          >
            <div className='metrics-comparison-table__cell metrics-comparison-table__cell--metric'>
              <span className='metrics-comparison-table__metric-name'>
                {metric.name}
              </span>
              <span
                className={`metrics-comparison-table__type-badge metrics-comparison-table__type-badge--${metric.type}`}
              >
                {metric.type === 'primary' ? 'Primary' : 'Secondary'}
              </span>
            </div>
            <div className='metrics-comparison-table__cell metrics-comparison-table__cell--value'>
              {metric.control}
            </div>
            <div className='metrics-comparison-table__cell metrics-comparison-table__cell--value'>
              {metric.variant}
            </div>
            <div className='metrics-comparison-table__cell metrics-comparison-table__cell--lift'>
              <div className='metrics-comparison-table__lift-bar'>
                <div
                  style={{
                    width: `${
                      50 -
                      (metric.liftDirection === 'negative' ? liftPercent : 0)
                    }%`,
                  }}
                />
                <div
                  className={`metrics-comparison-table__lift-fill metrics-comparison-table__lift-fill--${metric.liftDirection}`}
                  style={{ width: `${liftPercent}%` }}
                />
              </div>
              <span
                className={`metrics-comparison-table__lift-value metrics-comparison-table__lift-value--${metric.liftDirection}`}
              >
                {metric.liftValue > 0 ? '+' : ''}
                {metric.liftValue}%
              </span>
            </div>
            <div
              className={`metrics-comparison-table__cell metrics-comparison-table__cell--significance metrics-comparison-table__significance--${
                metric.isSignificant ? 'significant' : 'not-significant'
              }`}
            >
              {metric.significance}
              {metric.isSignificant && (
                <span className='metrics-comparison-table__check'>
                  {' '}
                  &#10003;
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default MetricsComparisonTable
