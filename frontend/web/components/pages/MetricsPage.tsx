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
          <div className='metrics-page__banner'>
            <span className='metrics-page__banner-text'>
              <Icon
                name='layers'
                width={16}
                className='metrics-page__banner-icon'
              />
              Metrics are computed from your <strong>{warehouseLabel}</strong>{' '}
              warehouse.
            </span>
            <a
              className='metrics-page__banner-link'
              onClick={() => history.push(settingsUrl)}
            >
              Manage connection
            </a>
          </div>
        )}

        <div className='metrics-page__controls'>
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

        <div className='metrics-page__list'>
          {metrics.map((metric) => (
            <div key={metric.id} className='metrics-page__row'>
              <div className='metrics-page__row-main'>
                <span className='metrics-page__row-name'>{metric.name}</span>
                {!!metric.description && (
                  <span className='metrics-page__row-desc'>
                    {metric.description}
                  </span>
                )}
              </div>
              <span className='metrics-page__row-agg'>
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
