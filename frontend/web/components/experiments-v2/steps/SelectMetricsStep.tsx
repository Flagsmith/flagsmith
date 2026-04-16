import React, { FC, useMemo, useState } from 'react'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import { Metric, MOCK_METRICS } from 'components/experiments-v2/types'
import './SelectMetricsStep.scss'

type SelectMetricsStepProps = {
  availableMetrics?: Metric[]
  selectedMetrics: Metric[]
  onToggleMetric: (metric: Metric) => void
}

const SelectMetricsStep: FC<SelectMetricsStepProps> = ({
  availableMetrics = MOCK_METRICS,
  onToggleMetric,
  selectedMetrics,
}) => {
  const [search, setSearch] = useState('')

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

  const getBadge = (metric: Metric) => {
    const role = getRole(metric)
    if (!isSelected(metric) || !role) return undefined
    return {
      label: role === 'primary' ? 'Primary' : 'Secondary',
      variant: role as 'primary' | 'secondary',
    }
  }

  if (availableMetrics.length === 0) {
    return (
      <div className='select-metrics-step'>
        <EmptyState
          title='No metrics yet'
          description='Create your first metric to start measuring experiment outcomes.'
          icon='bar-chart'
          action={
            <Button theme='primary' size='small'>
              Create Metric
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className='select-metrics-step'>
      <Input
        value={search}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setSearch(e.target.value)
        }
        placeholder='Search metrics...'
        search
      />

      {filteredMetrics.length > 0 ? (
        <div className='select-metrics-step__list'>
          {filteredMetrics.map((metric) => (
            <SelectableCard
              key={metric.id}
              title={metric.name}
              description={metric.description}
              selected={isSelected(metric)}
              badge={getBadge(metric)}
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
            <Button theme='primary' size='small'>
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
