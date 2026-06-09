import { ChangeEvent, FC, useEffect, useState } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { useRouteContext } from 'components/providers/RouteContext'
import {
  useCreateMetricMutation,
  useGetMetricsQuery,
} from 'common/services/useMetric'
import { useGetWarehouseConnectionsQuery } from 'common/services/useWarehouseConnection'
import { WarehouseType } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import PageTitle from 'components/PageTitle'
import CreateMetricForm from 'components/experiments/CreateMetricForm'
import {
  buildMetricPayload,
  DEFAULT_METRIC_DEFINITION_VERSION,
  MetricFormState,
} from 'components/experiments/CreateMetricForm/utils'
import './MetricsPage.scss'

const WAREHOUSE_TYPE_LABEL: Record<WarehouseType, string> = {
  clickhouse: 'ClickHouse',
  flagsmith: 'Flagsmith',
  snowflake: 'Snowflake',
}

const MetricsPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const history = useHistory()
  const location = useLocation()
  const [searchInput, setSearchInput] = useState('')
  const [createMetric, { isLoading: isSaving }] = useCreateMetricMutation()

  const isEnabled = Utils.getFlagsmithHasFeature('experiment_metrics')
  const isCreating =
    new URLSearchParams(location.search).get('create') === 'true'

  useEffect(() => {
    if (!isEnabled && environmentId && projectId) {
      history.replace(
        `/project/${projectId}/environment/${environmentId}/features`,
      )
    }
  }, [isEnabled, environmentId, projectId, history])

  const { data: metricsData, isLoading } = useGetMetricsQuery(
    { environmentId: environmentId ?? '' },
    { skip: !environmentId || !isEnabled },
  )

  const { data: warehouseConnections } = useGetWarehouseConnectionsQuery(
    { environmentId: environmentId ?? '' },
    { skip: !environmentId || !isEnabled },
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

  const handleSubmit = async (state: MetricFormState) => {
    const version =
      Number(Utils.getFlagsmithValue('experiment_metrics')) ||
      DEFAULT_METRIC_DEFINITION_VERSION
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

  if (isCreating) {
    return (
      <div data-test='metrics-page' className='app-container container'>
        <PageTitle title='Create Metric'>
          Metrics capture the outcomes your experiments measure.
        </PageTitle>
        <CreateMetricForm
          isSaving={isSaving}
          onCancel={() => history.push(metricsPath)}
          onSubmit={handleSubmit}
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
    if (!metrics?.length) {
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
            <span className='metrics-page__banner-text d-flex align-items-center gap-2 text-secondary'>
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

        <div className='metrics-page__list d-flex flex-column rounded-md'>
          {metrics.map((metric) => (
            <div
              key={metric.id}
              className='metrics-page__row d-flex align-items-center justify-content-between gap-3'
            >
              <div className='metrics-page__row-main d-flex flex-column'>
                <span className='metrics-page__row-name text-default'>
                  {metric.name}
                </span>
                {!!metric.description && (
                  <span className='metrics-page__row-desc text-secondary'>
                    {metric.description}
                  </span>
                )}
              </div>
              <span className='metrics-page__row-agg text-secondary'>
                {metric.aggregation}
              </span>
            </div>
          ))}
        </div>
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
