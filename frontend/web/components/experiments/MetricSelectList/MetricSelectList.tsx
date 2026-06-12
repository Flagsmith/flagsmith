import { ChangeEvent, FC, useEffect, useState } from 'react'
import { Metric } from 'common/types/responses'
import { useGetMetricsQuery } from 'common/services/useMetric'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
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
      <div className='text-center py-5'>
        <Icon
          name='bar-chart'
          width={48}
          className='text-muted mb-3 d-block mx-auto'
        />
        <h5>No metrics yet</h5>
        <p className='text-muted mb-4'>
          Create your first metric to measure experiment outcomes.
        </p>
        <Button onClick={onCreateClick}>
          <Icon name='plus' width={16} />
          Create Metric
        </Button>
      </div>
    )
  }

  return (
    <div className='d-flex flex-column gap-3'>
      <div className='d-flex align-items-center gap-3'>
        <div className='flex-fill'>
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
          <div className='d-flex flex-column gap-3'>
            {metrics.map((metric) => {
              const isSelected = selectedMetric?.id === metric.id
              return (
                <button
                  type='button'
                  key={metric.id}
                  className={`metric-select-card text-left rounded-lg p-3 ${
                    isSelected ? 'metric-select-card--selected' : ''
                  }`}
                  onClick={() => onSelect(metric)}
                >
                  <div className='d-flex align-items-start justify-content-between gap-3'>
                    <div className='d-flex flex-column gap-1'>
                      <span className='metric-select-card__name'>
                        {metric.name}
                      </span>
                      {!!metric.description && (
                        <span className='text-secondary'>
                          {metric.description}
                        </span>
                      )}
                      <div className='d-flex flex-wrap gap-2 mt-1'>
                        <span className='bg-surface-subtle rounded-sm px-2 py-1 fs-small text-secondary'>
                          {metric.definition.event}: {metric.aggregation}
                        </span>
                        <span className='bg-surface-subtle rounded-sm px-2 py-1 fs-small text-secondary'>
                          {METRIC_DIRECTION_LABELS[metric.direction]}
                        </span>
                      </div>
                    </div>
                    {isSelected && (
                      <span className='bg-surface-action rounded-full px-3 py-1 fs-small text-white flex-shrink-0'>
                        Primary
                      </span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
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
        </>
      ) : (
        <div className='text-center py-4'>
          <p className='text-muted mb-0'>No metrics match your search.</p>
        </div>
      )}
    </div>
  )
}

export default MetricSelectList
