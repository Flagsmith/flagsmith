import React, { FC, useMemo, useState } from 'react'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import WarningMessage from 'components/WarningMessage'
import CreateMetricForm from 'components/experiments-v2/shared/CreateMetricForm'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import {
  Metric,
  MetricDirection,
  MOCK_METRICS,
} from 'components/experiments-v2/types'
import './SelectMetricsStep.scss'

const directionTag = (d: MetricDirection): string => {
  if (d === 'higher-better') return '↑ higher is better'
  if (d === 'lower-better') return '↓ lower is better'
  return '— neither'
}

type SelectMetricsStepProps = {
  availableMetrics?: Metric[]
  selectedMetrics: Metric[]
  onToggleMetric: (metric: Metric) => void
  onSetPrimaryMetric?: (metricId: string) => void
}

const SelectMetricsStep: FC<SelectMetricsStepProps> = ({
  availableMetrics: availableMetricsProp = MOCK_METRICS,
  onSetPrimaryMetric,
  onToggleMetric,
  selectedMetrics,
}) => {
  const [search, setSearch] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createdMetrics, setCreatedMetrics] = useState<Metric[]>([])

  const availableMetrics = useMemo(
    () => [...availableMetricsProp, ...createdMetrics],
    [availableMetricsProp, createdMetrics],
  )

  const filteredMetrics = useMemo(() => {
    if (!search) return availableMetrics
    const lower = search.toLowerCase()
    return availableMetrics.filter(
      (m) =>
        m.name.toLowerCase().includes(lower) ||
        m.description.toLowerCase().includes(lower),
    )
  }, [search, availableMetrics])

  const isSelected = (metric: Metric) =>
    selectedMetrics.some((m) => m.id === metric.id)

  const getRole = (metric: Metric) =>
    selectedMetrics.find((m) => m.id === metric.id)?.role

  const getPrimaryToggle = (metric: Metric) => {
    if (!isSelected(metric) || !onSetPrimaryMetric) return undefined
    return {
      isPrimary: getRole(metric) === 'primary',
      onSetPrimary: () => onSetPrimaryMetric(metric.id),
    }
  }

  const primaryCount = selectedMetrics.filter(
    (m) => m.role === 'primary',
  ).length

  const handleCreate = (metric: Metric) => {
    setCreatedMetrics((prev) => [...prev, metric])
    onToggleMetric(metric)
    setIsCreating(false)
    setSearch('')
  }

  if (isCreating) {
    return (
      <div className='select-metrics-step'>
        <CreateMetricForm
          onCancel={() => setIsCreating(false)}
          onSubmit={handleCreate}
        />
      </div>
    )
  }

  if (availableMetrics.length === 0) {
    return (
      <div className='select-metrics-step'>
        <EmptyState
          title='No metrics yet'
          description='Create your first metric to start measuring experiment outcomes.'
          icon='bar-chart'
          action={
            <Button
              theme='primary'
              size='small'
              onClick={() => setIsCreating(true)}
            >
              Create Metric
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className='select-metrics-step'>
      <div className='select-metrics-step__toolbar'>
        <div className='select-metrics-step__search'>
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
          theme='outline'
          size='small'
          iconLeft='plus'
          onClick={() => setIsCreating(true)}
        >
          Create Metric
        </Button>
      </div>

      {primaryCount > 1 && (
        <WarningMessage
          warningMessage={
            <span>
              You have {primaryCount} primary metrics. Best practice is{' '}
              <strong>one primary metric</strong> to avoid multiple-comparisons
              issues — pick the single metric you most want to move and demote
              the rest to secondary.
            </span>
          }
        />
      )}

      {filteredMetrics.length > 0 ? (
        <div className='select-metrics-step__list'>
          {filteredMetrics.map((metric) => (
            <SelectableCard
              key={metric.id}
              title={metric.name}
              description={metric.description}
              selected={isSelected(metric)}
              primaryToggle={getPrimaryToggle(metric)}
              tags={[
                `conversion: ${metric.measurementType}`,
                directionTag(metric.direction),
              ]}
              onClick={() => onToggleMetric(metric)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title={`No metrics found for "${search}"`}
          description='Try a different search term, or create a new metric.'
          icon='search'
          action={
            <Button
              theme='primary'
              size='small'
              onClick={() => setIsCreating(true)}
            >
              Create Metric
            </Button>
          }
        />
      )}
    </div>
  )
}

SelectMetricsStep.displayName = 'SelectMetricsStep'
export default SelectMetricsStep
