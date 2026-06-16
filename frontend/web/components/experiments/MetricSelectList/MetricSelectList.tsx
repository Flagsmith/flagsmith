import { ChangeEvent, FC, useEffect, useState } from 'react'
import { Metric } from 'common/types/responses'
import { useGetMetricsQuery } from 'common/services/useMetric'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import SelectableCard from 'components/base/SelectableCard'
import EmptyState from 'components/EmptyState'
import Icon from 'components/icons/Icon'
import Paging from 'components/Paging'
import { METRIC_DIRECTION_LABELS } from 'components/experiments/constants'
import './MetricSelectList.scss'

const PAGE_SIZE = 5

type MetricSelectListProps = {
  environmentId: string
  selectedMetric: Metric | null
  onSelect: (metric: Metric) => void
  onCreateClick: () => void
}

const MetricSelectList: FC<MetricSelectListProps> = ({
  environmentId,
  onCreateClick,
  onSelect,
  selectedMetric,
}) => {
  const { search, searchInput, setSearchInput } = useDebouncedSearch()
  const [page, setPage] = useState(1)

  useEffect(() => {
    setPage(1)
  }, [search])

  const { data: metricsData, isLoading } = useGetMetricsQuery(
    {
      environmentId,
      page,
      page_size: PAGE_SIZE,
      q: search || undefined,
    },
    { skip: !environmentId },
  )

  const metrics = metricsData?.results
  const metricCount = metricsData?.count ?? 0
  const hasActiveSearch = !!search

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (metricCount === 0 && !hasActiveSearch) {
    return (
      <EmptyState
        title='No metrics yet'
        description='Create your first metric to measure experiment outcomes.'
        icon='bar-chart'
        action={
          <Button onClick={onCreateClick}>
            <Icon name='plus' width={16} />
            Create Metric
          </Button>
        }
      />
    )
  }

  return (
    <div className='metric-select-list'>
      <div className='metric-select-list__toolbar'>
        <div className='metric-select-list__search'>
          <Input
            value={searchInput}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setSearchInput(Utils.safeParseEventValue(e))
            }
            placeholder='Search metrics...'
            search
            size='small'
          />
        </div>
        <Button theme='outline' onClick={onCreateClick}>
          <Icon name='plus' width={16} />
          Create Metric
        </Button>
      </div>

      {metrics?.length ? (
        <>
          <div className='metric-select-list__cards'>
            {metrics.map((metric) => {
              const isSelected = selectedMetric?.id === metric.id
              return (
                <SelectableCard
                  key={metric.id}
                  title={metric.name}
                  description={metric.description || ''}
                  selected={isSelected}
                  badge={
                    isSelected
                      ? { label: 'Primary', variant: 'primary' }
                      : undefined
                  }
                  tags={[
                    `${metric.definition.event}: ${metric.aggregation}`,
                    METRIC_DIRECTION_LABELS[metric.direction],
                  ]}
                  onClick={() => onSelect(metric)}
                />
              )
            })}
          </div>
          {metricCount > PAGE_SIZE && (
            <Paging
              className='border-top-0'
              paging={{
                ...(metricsData || {}),
                page,
                pageSize: PAGE_SIZE,
              }}
              nextPage={() => setPage(page + 1)}
              prevPage={() => setPage(page - 1)}
              goToPage={(p: number) => setPage(p)}
              isLoading={isLoading}
            />
          )}
        </>
      ) : (
        <EmptyState
          title={`No metrics found for "${search}"`}
          description='Try a different search term, or create a new metric.'
          icon='search'
        />
      )}
    </div>
  )
}

export default MetricSelectList
