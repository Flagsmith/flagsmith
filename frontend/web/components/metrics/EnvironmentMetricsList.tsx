import React, { FC, useEffect } from 'react'
import AccordionCard from 'components/base/accordion/AccordionCard'
import { useGetEnvironmentMetricsQuery } from 'common/services/useEnvironment'
import EnvironmentMetric from './EnvironmentMetric'

interface EnvironmentMetricsListProps {
  environmentApiKey: string
  forceRefetch?: boolean
}

const EnvironmentMetricsList: FC<EnvironmentMetricsListProps> = ({
  environmentApiKey,
  forceRefetch,
}) => {
  const { data, refetch } = useGetEnvironmentMetricsQuery({
    id: environmentApiKey,
  })
  const MAX_COLUMNS = 6
  const columns = Math.min(data?.metrics?.length || 0, MAX_COLUMNS) || 1

  useEffect(() => {
    if (forceRefetch) {
      refetch()
    }
  }, [forceRefetch, refetch])

  if (!data || data.metrics.length === 0) {
    return null
  }

  return (
    <div className='mb-3'>
      <AccordionCard title='Summary'>
        <div className='flex gap-2 mt-4'>
          <div
            className='metrics-grid'
            style={{
              alignItems: 'stretch',
              display: 'grid',
              gridTemplateColumns: `repeat(${columns}, 1fr)`,
              justifyContent: 'center',
              rowGap: 12,
            }}
          >
            {data?.metrics.map((metric) => (
              <EnvironmentMetric
                key={metric.name}
                label={metric.description}
                value={metric.value}
              />
            ))}
          </div>
        </div>
      </AccordionCard>
    </div>
  )
}

export default EnvironmentMetricsList
