import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import { MetricComparison } from 'components/experiments-v2/types'
import './MetricsComparisonTable.scss'

type MetricsComparisonTableProps = {
  metrics: MetricComparison[]
}

const MetricsComparisonTable: FC<MetricsComparisonTableProps> = ({
  metrics,
}) => {
  return (
    <div className='metrics-comparison-table'>
      <div className='metrics-comparison-table__head'>
        <span className='metrics-comparison-table__th'>Metric</span>
        <span className='metrics-comparison-table__th'>Control</span>
        <span className='metrics-comparison-table__th'>Treatment B</span>
        <span className='metrics-comparison-table__th'>Lift</span>
        <span className='metrics-comparison-table__th'>Significance</span>
      </div>

      {metrics.map((metric) => (
        <div key={metric.name} className='metrics-comparison-table__row'>
          <span className='metrics-comparison-table__td'>{metric.name}</span>
          <span className='metrics-comparison-table__td metrics-comparison-table__td--mono'>
            {metric.control}
          </span>
          <span className='metrics-comparison-table__td metrics-comparison-table__td--mono'>
            {metric.treatment}
          </span>
          <span
            className={`metrics-comparison-table__td metrics-comparison-table__td--mono metrics-comparison-table__td--${metric.liftDirection}`}
          >
            {metric.lift}
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
      ))}
    </div>
  )
}

MetricsComparisonTable.displayName = 'MetricsComparisonTable'
export default MetricsComparisonTable
