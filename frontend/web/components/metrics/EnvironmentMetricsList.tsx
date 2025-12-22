import React, { FC, useEffect } from 'react'
import AccordionCard from 'components/base/accordion/AccordionCard'
import { useGetEnvironmentMetricsQuery } from 'common/services/useEnvironment'
import EnvironmentMetric from './EnvironmentMetric'
import { getExtraMetricsData } from './constants'

interface EnvironmentMetricsListProps {
  environmentId: string
  projectId: number
  forceRefetch?: boolean
}

const EnvironmentMetricsList: FC<EnvironmentMetricsListProps> = ({
  environmentId,
  forceRefetch,
  projectId,
}) => {
  const { data, isLoading, refetch } = useGetEnvironmentMetricsQuery(
    {
      id: environmentId,
    },
    {
      skip: !environmentId,
    },
  )

  const MAX_COLUMNS = 6
  const columns = Math.min(data?.metrics?.length || 0, MAX_COLUMNS) || 1

  const extraMetricsData = getExtraMetricsData(projectId, environmentId)

  useEffect(() => {
    if (forceRefetch) {
      refetch()
    }
  }, [forceRefetch, refetch])

  return (
    <div className='mb-3'>
      <AccordionCard title='Summary' isLoading={isLoading}>
        <div className='flex gap-2 mt-4'>
          <div
            className='metrics-grid'
            style={{
              gridTemplateColumns: `repeat(${columns}, 1fr)`,
            }}
          >
            {data?.metrics.map((metric) => (
              <EnvironmentMetric
                key={metric.name}
                label={metric.description}
                value={metric.value}
                link={extraMetricsData?.[metric.name]?.link}
                tooltip={extraMetricsData?.[metric.name]?.tooltip}
              />
            ))}
          </div>
        </div>
      </AccordionCard>
    </div>
  )
}

export default EnvironmentMetricsList
