import { ChangeEvent, FC, useEffect, useState } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { useRouteContext } from 'components/providers/RouteContext'
import {
  useCreateMetricMutation,
  useDeleteMetricMutation,
  useGetMetricQuery,
  useGetMetricsQuery,
  useUpdateMetricMutation,
} from 'common/services/useMetric'
import { useGetWarehouseConnectionsQuery } from 'common/services/useWarehouseConnection'
import { Metric, WarehouseType } from 'common/types/responses'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import PageTitle from 'components/PageTitle'
import Paging from 'components/Paging'
import CreateMetricForm from 'components/experiments/CreateMetricForm'
import CreateMetricFormSkeleton from 'components/experiments/CreateMetricForm/CreateMetricFormSkeleton'
import MetricsTable from 'components/experiments/MetricsTable/MetricsTable'
import {
  buildMetricPayload,
  DEFAULT_METRIC_DEFINITION_VERSION,
  metricToFormState,
  MetricFormState,
} from 'components/experiments/CreateMetricForm/utils'
import './MetricsPage.scss'

const WAREHOUSE_TYPE_LABEL: Record<WarehouseType, string> = {
  clickhouse: 'ClickHouse',
  flagsmith: 'Flagsmith',
  snowflake: 'Snowflake',
}

const PAGE_SIZE = 10

const MetricsPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const history = useHistory()
  const location = useLocation()
  const { search, searchInput, setSearchInput } = useDebouncedSearch()
  const [page, setPage] = useState(1)
  const [createMetric, { isLoading: isCreatingMetric }] =
    useCreateMetricMutation()
  const [updateMetric, { isLoading: isUpdatingMetric }] =
    useUpdateMetricMutation()
  const [deleteMetric] = useDeleteMetricMutation()

  const isEnabled = Utils.getFlagsmithHasFeature('experiment_metrics')
  const params = new URLSearchParams(location.search)
  const isCreating = params.get('create') === 'true'
  const editParam = params.get('edit')
  const editingId =
    editParam && !isNaN(Number(editParam)) ? Number(editParam) : null

  useEffect(() => {
    if (!isEnabled && environmentId && projectId) {
      history.replace(
        `/project/${projectId}/environment/${environmentId}/features`,
      )
    }
  }, [isEnabled, environmentId, projectId, history])

  useEffect(() => {
    setPage(1)
  }, [search])

  const { data: metricsData, isLoading } = useGetMetricsQuery(
    {
      environmentId: environmentId ?? '',
      page,
      page_size: PAGE_SIZE,
      q: search || undefined,
    },
    { skip: !environmentId || !isEnabled },
  )

  const { data: warehouseConnections } = useGetWarehouseConnectionsQuery(
    { environmentId: environmentId ?? '', exclude_event_stats: true },
    { skip: !environmentId || !isEnabled },
  )

  const { data: editedMetric, isFetching: isFetchingEditedMetric } =
    useGetMetricQuery(
      { environmentId: environmentId ?? '', metricId: editingId ?? 0 },
      { skip: !environmentId || !isEnabled || editingId === null },
    )

  if (!environmentId || !projectId || !isEnabled) return null

  const connection = warehouseConnections?.[0]
  const warehouseLabel = connection
    ? WAREHOUSE_TYPE_LABEL[connection.warehouse_type] ??
      connection.warehouse_type
    : ''
  const settingsUrl = `/project/${projectId}/environment/${environmentId}/settings?tab=warehouse`
  const metricsPath = `/project/${projectId}/environment/${environmentId}/metrics`
  const metrics = metricsData?.results
  const metricCount = metricsData?.count ?? 0
  const hasActiveSearch = !!search
  const version =
    Number(Utils.getFlagsmithValue('experiment_metrics')) ||
    DEFAULT_METRIC_DEFINITION_VERSION

  const handleCreate = async (state: MetricFormState) => {
    try {
      await createMetric({
        body: buildMetricPayload(state, version),
        environmentId,
      }).unwrap()
      toast('Metric created successfully')
      history.push(metricsPath)
    } catch {
      toast('Failed to create metric', 'danger')
    }
  }

  const handleUpdate = (metric: Metric) => async (state: MetricFormState) => {
    try {
      await updateMetric({
        body: buildMetricPayload(state, version),
        environmentId,
        metricId: metric.id,
      }).unwrap()
      toast('Metric updated successfully')
      history.push(metricsPath)
    } catch {
      toast('Failed to update metric', 'danger')
    }
  }

  const handleDelete = (metric: Metric) => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to delete <strong>{metric.name}</strong>? This
          cannot be undone.
        </div>
      ),
      destructive: true,
      onYes: async () => {
        try {
          await deleteMetric({ environmentId, metricId: metric.id }).unwrap()
          toast('Metric deleted')
        } catch (e: any) {
          toast(e?.data?.detail || 'Failed to delete metric', 'danger')
        }
      },
      title: 'Delete Metric',
      yesText: 'Delete',
    })
  }

  if (isCreating) {
    return (
      <div data-test='metrics-page' className='app-container container'>
        <PageTitle title='Create Metric'>
          Metrics capture the outcomes your experiments measure.
        </PageTitle>
        <CreateMetricForm
          isSaving={isCreatingMetric}
          onCancel={() => history.push(metricsPath)}
          onSubmit={handleCreate}
        />
      </div>
    )
  }

  if (editingId) {
    const metric = metrics?.find((m) => m.id === editingId) ?? editedMetric
    if (!metric) {
      return (
        <div data-test='metrics-page' className='app-container container'>
          <PageTitle title='Edit Metric' />
          {isFetchingEditedMetric ? (
            <CreateMetricFormSkeleton />
          ) : (
            <div className='text-center py-5'>
              <p className='text-danger mb-4'>Metric not found.</p>
              <Button onClick={() => history.push(metricsPath)}>
                Back to Metrics
              </Button>
            </div>
          )}
        </div>
      )
    }
    return (
      <div data-test='metrics-page' className='app-container container'>
        <PageTitle title='Edit Metric'>
          Update how this metric is measured.
        </PageTitle>
        <CreateMetricForm
          key={metric.id}
          initialState={metricToFormState(metric)}
          isSaving={isUpdatingMetric}
          submitLabel='Save changes'
          onCancel={() => history.push(metricsPath)}
          onSubmit={handleUpdate(metric)}
        />
      </div>
    )
  }

  const renderBody = () => {
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
          <Button onClick={() => history.push(`${metricsPath}?create=true`)}>
            <Icon name='plus' width={16} />
            Create Metric
          </Button>
        </div>
      )
    }
    return (
      <>
        {!!connection && (
          <div className='metrics-page__banner d-flex align-items-center justify-content-between gap-3 mb-3 rounded-md bg-surface-subtle'>
            <span className='metrics-page__banner-text d-flex align-items-center gap-2'>
              <Icon name='layers' width={16} className='text-action' />
              Metrics are computed from your <strong>
                {warehouseLabel}
              </strong>{' '}
              warehouse.
            </span>
            <a
              className='metrics-page__banner-link flex-shrink-0 text-action'
              onClick={() => history.push(settingsUrl)}
            >
              Manage connection
            </a>
          </div>
        )}

        <div className='metrics-page__controls d-flex align-items-center mb-3'>
          <div className='metrics-page__search'>
            <Input
              value={searchInput}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setSearchInput(Utils.safeParseEventValue(e))
              }
              placeholder='Search metrics...'
              search
            />
          </div>
          <Button onClick={() => history.push(`${metricsPath}?create=true`)}>
            <Icon name='plus' width={16} />
            Create Metric
          </Button>
        </div>

        {metrics?.length ? (
          <>
            <MetricsTable
              metrics={metrics}
              onEdit={(metric) =>
                history.push(`${metricsPath}?edit=${metric.id}`)
              }
              onDelete={handleDelete}
            />
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
          <div className='text-center py-5'>
            <p className='text-muted'>No metrics match your search.</p>
          </div>
        )}
      </>
    )
  }

  return (
    <div data-test='metrics-page' className='app-container container'>
      <PageTitle title='Metrics'>
        Metrics track the outcomes you measure across experiments. Each
        experiment picks one as its primary; the rest are observed for context.
      </PageTitle>
      {renderBody()}
    </div>
  )
}

MetricsPage.displayName = 'MetricsPage'
export default MetricsPage
