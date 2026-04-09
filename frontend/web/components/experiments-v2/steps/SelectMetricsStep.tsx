import React, { FC, useMemo, useState } from 'react'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import { Metric, MOCK_METRICS } from 'components/experiments-v2/types'
import './SelectMetricsStep.scss'

type SelectMetricsStepProps = {
  selectedMetrics: Metric[]
  onToggleMetric: (metric: Metric) => void
}

const SelectMetricsStep: FC<SelectMetricsStepProps> = ({
  onToggleMetric,
  selectedMetrics,
}) => {
  const [search, setSearch] = useState('')

  const filteredMetrics = useMemo(() => {
    if (!search) return MOCK_METRICS
    const lower = search.toLowerCase()
    return MOCK_METRICS.filter(
      (m) =>
        m.name.toLowerCase().includes(lower) ||
        m.description.toLowerCase().includes(lower),
    )
  }, [search])

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
        <div className='select-metrics-step__empty'>
          <Icon name='search' width={36} />
          <span className='select-metrics-step__empty-title'>
            No metrics found for &ldquo;{search}&rdquo;
          </span>
          <span className='select-metrics-step__empty-desc'>
            Try a different search term, or define a custom metric with SQL
          </span>
          <Button theme='primary' size='small'>
            Define Custom Metric
          </Button>
        </div>
      )}
    </div>
  )
}

SelectMetricsStep.displayName = 'SelectMetricsStep'
export default SelectMetricsStep
