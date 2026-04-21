import React, { FC, useMemo, useState } from 'react'
import AccountStore from 'common/stores/account-store'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import CreateMetricForm from './shared/CreateMetricForm'
import { Metric, MOCK_METRICS } from './types'
import './MetricsLibraryPage.scss'

type Mode =
  | { kind: 'list' }
  | { kind: 'create' }
  | { kind: 'edit'; metric: Metric }

const MetricsLibraryPage: FC = () => {
  const [metrics, setMetrics] = useState<Metric[]>(MOCK_METRICS)
  const [search, setSearch] = useState('')
  const [mode, setMode] = useState<Mode>({ kind: 'list' })
  const organisationId = AccountStore.getOrganisation()?.id
  const warehouseUrl = organisationId
    ? `/organisation/${organisationId}/warehouse`
    : undefined

  const filtered = useMemo(() => {
    if (!search) return metrics
    const lower = search.toLowerCase()
    return metrics.filter(
      (m) =>
        m.name.toLowerCase().includes(lower) ||
        m.description.toLowerCase().includes(lower),
    )
  }, [metrics, search])

  const handleCreateOrEditSubmit = (metric: Metric) => {
    setMetrics((prev) => {
      const existing = prev.findIndex((m) => m.id === metric.id)
      if (existing >= 0) {
        const next = [...prev]
        next[existing] = metric
        return next
      }
      return [metric, ...prev]
    })
    setMode({ kind: 'list' })
  }

  const handleDelete = (metric: Metric) => {
    openConfirm({
      body: (
        <span>
          Delete <strong>{metric.name}</strong>?{' '}
          {metric.usageCount > 0 ? (
            <>
              This metric is used by <strong>{metric.usageCount}</strong>{' '}
              experiment
              {metric.usageCount === 1 ? '' : 's'} — deleting it will remove it
              from those experiments.
            </>
          ) : (
            'This metric is not used by any experiments.'
          )}
        </span>
      ),
      destructive: true,
      onYes: () => setMetrics((prev) => prev.filter((m) => m.id !== metric.id)),
      title: 'Delete metric?',
      yesText: 'Delete',
    })
  }

  if (mode.kind === 'create' || mode.kind === 'edit') {
    return (
      <div className='metrics-library-page'>
        <CreateMetricForm
          initialValues={mode.kind === 'edit' ? mode.metric : undefined}
          onCancel={() => setMode({ kind: 'list' })}
          onSubmit={handleCreateOrEditSubmit}
        />
      </div>
    )
  }

  let listContent: React.ReactNode
  if (metrics.length === 0) {
    listContent = (
      <EmptyState
        title='No metrics yet'
        description='Create your first metric to start measuring experiment outcomes.'
        icon='bar-chart'
        action={
          <Button
            theme='primary'
            size='small'
            onClick={() => setMode({ kind: 'create' })}
          >
            Create Metric
          </Button>
        }
      />
    )
  } else if (filtered.length === 0) {
    listContent = (
      <EmptyState
        title={`No metrics found for "${search}"`}
        description='Try a different search term, or create a new metric.'
        icon='search'
      />
    )
  } else {
    listContent = (
      <div className='metrics-library-page__table'>
        <div className='metrics-library-page__head'>
          <span className='metrics-library-page__th metrics-library-page__th--name'>
            Name
          </span>
          <span className='metrics-library-page__th metrics-library-page__th--desc'>
            Description
          </span>
          <span className='metrics-library-page__th metrics-library-page__th--usage'>
            Used in
          </span>
          <span className='metrics-library-page__th metrics-library-page__th--updated'>
            Last updated
          </span>
          <span className='metrics-library-page__th metrics-library-page__th--actions' />
        </div>

        {filtered.map((metric) => (
          <div key={metric.id} className='metrics-library-page__row'>
            <span className='metrics-library-page__td metrics-library-page__td--name'>
              <span className='metrics-library-page__metric-name'>
                {metric.name}
              </span>
              {metric.source ? (
                <span className='metrics-library-page__source'>
                  <Icon name='layers' width={12} />
                  <code className='metrics-library-page__source-code'>
                    {metric.source.table}
                    {metric.source.eventName
                      ? ` · ${metric.source.eventName}`
                      : ''}
                    {metric.source.valueColumn
                      ? ` · ${metric.source.valueColumn}`
                      : ''}
                    {metric.source.filter ? ` · ${metric.source.filter}` : ''}
                  </code>
                </span>
              ) : (
                <span className='metrics-library-page__source metrics-library-page__source--missing'>
                  Source not configured
                </span>
              )}
            </span>
            <span className='metrics-library-page__td metrics-library-page__td--desc'>
              {metric.description}
            </span>
            <span className='metrics-library-page__td metrics-library-page__td--usage'>
              {metric.usageCount === 0
                ? 'Not in use'
                : `${metric.usageCount} experiment${
                    metric.usageCount === 1 ? '' : 's'
                  }`}
            </span>
            <span className='metrics-library-page__td metrics-library-page__td--updated'>
              {metric.lastUpdated}
            </span>
            <span className='metrics-library-page__td metrics-library-page__td--actions'>
              <button
                className='metrics-library-page__action-btn'
                onClick={() => setMode({ kind: 'edit', metric })}
                type='button'
                aria-label={`Edit ${metric.name}`}
              >
                <Icon name='edit' width={16} />
              </button>
              <button
                className='metrics-library-page__action-btn metrics-library-page__action-btn--danger'
                onClick={() => handleDelete(metric)}
                type='button'
                aria-label={`Delete ${metric.name}`}
              >
                <Icon name='trash-2' width={16} />
              </button>
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className='app-container container metrics-library-page'>
      <div className='metrics-library-page__header'>
        <div>
          <h3 className='metrics-library-page__title'>Metrics</h3>
          <p className='metrics-library-page__subtitle text-muted'>
            Metrics track the outcomes you measure across experiments. Primary
            and secondary metrics drive experiment verdicts; guardrails flag
            regressions.
          </p>
        </div>
      </div>

      <div className='metrics-library-page__source-banner'>
        <Icon name='layers' width={16} />
        <span>
          Metrics are computed from your <strong>Snowflake</strong> warehouse (
          <code>FLAGSMITH_PROD.PUBLIC</code>).{' '}
        </span>
        {warehouseUrl && (
          <a
            className='metrics-library-page__source-banner-link'
            href={warehouseUrl}
          >
            Manage connection &rarr;
          </a>
        )}
      </div>

      <div className='metrics-library-page__toolbar'>
        <div className='metrics-library-page__search'>
          <Input
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearch(e.target.value)
            }
            placeholder='Search metrics...'
            search
          />
        </div>
        <Button
          theme='primary'
          size='small'
          iconLeft='plus'
          onClick={() => setMode({ kind: 'create' })}
        >
          Create Metric
        </Button>
      </div>

      {listContent}
    </div>
  )
}

MetricsLibraryPage.displayName = 'MetricsLibraryPage'
export default MetricsLibraryPage
