import React, { CSSProperties, FC } from 'react'
import Icon from 'components/icons/Icon'
import { MetricComparison } from 'components/experiments-v2/types'
import './MetricsComparisonTable.scss'

type MetricsComparisonTableProps = {
  metrics: MetricComparison[]
}

type LiftBarStyle = CSSProperties & { '--lift-bar-width': string }

const MetricsComparisonTable: FC<MetricsComparisonTableProps> = ({
  metrics,
}) => {
  const maxMagnitude = metrics.reduce(
    (max, m) => Math.max(max, Math.abs(m.liftValue)),
    0,
  )

  return (
    <div className='metrics-comparison-table'>
      <div className='metrics-comparison-table__head'>
        <span className='metrics-comparison-table__th'>Metric</span>
        <span className='metrics-comparison-table__th'>Control</span>
        <span className='metrics-comparison-table__th'>Treatment B</span>
        <span className='metrics-comparison-table__th metrics-comparison-table__th--lift'>
          Lift
        </span>
        <span className='metrics-comparison-table__th'>Significance</span>
      </div>

      {metrics.map((metric) => {
        const barWidthPercent =
          maxMagnitude === 0
            ? 0
            : (Math.abs(metric.liftValue) / maxMagnitude) * 50
        const barStyle: LiftBarStyle = {
          '--lift-bar-width': `${barWidthPercent}%`,
        }
        const side = metric.liftValue >= 0 ? 'right' : 'left'
        let tone: 'positive' | 'negative' | 'neutral' = 'neutral'
        if (metric.isSignificant) {
          tone = metric.liftDirection === 'negative' ? 'negative' : 'positive'
        }

        return (
          <div key={metric.name} className='metrics-comparison-table__row'>
            <span className='metrics-comparison-table__td'>{metric.name}</span>
            <span className='metrics-comparison-table__td metrics-comparison-table__td--mono'>
              {metric.control}
            </span>
            <span className='metrics-comparison-table__td metrics-comparison-table__td--mono'>
              {metric.treatment}
            </span>
            <span className='metrics-comparison-table__td metrics-comparison-table__td--lift'>
              <span
                className={`metrics-comparison-table__lift-bar metrics-comparison-table__lift-bar--side-${side} metrics-comparison-table__lift-bar--tone-${tone}`}
                aria-hidden='true'
              >
                <span className='metrics-comparison-table__lift-bar-axis' />
                <span
                  className='metrics-comparison-table__lift-bar-fill'
                  style={barStyle}
                />
              </span>
              <span
                className={`metrics-comparison-table__lift-label metrics-comparison-table__lift-label--${tone}`}
              >
                {metric.lift}
              </span>
            </span>
            <span
              className={`metrics-comparison-table__td metrics-comparison-table__td--significance ${
                metric.isSignificant
                  ? 'metrics-comparison-table__td--significant'
                  : ''
              }`}
            >
              {metric.significance}
              {metric.isSignificant && (
                <>
                  {' '}
                  <Icon name='checkmark' width={14} />
                </>
              )}
            </span>
          </div>
        )
      })}
    </div>
  )
}

MetricsComparisonTable.displayName = 'MetricsComparisonTable'
export default MetricsComparisonTable
