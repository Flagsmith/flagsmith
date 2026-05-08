import React, { FC, useMemo, useState } from 'react'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import Icon from 'components/icons/Icon'
import WarningMessage from 'components/WarningMessage'
import CreateMetricForm from 'components/experiments-v2/shared/CreateMetricForm'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import {
  INCLUSION_CRITERIA_LABELS,
  InclusionCriteria,
  MULTI_VARIANT_HANDLING_LABELS,
  Metric,
  MetricDirection,
  MetricRole,
  MOCK_METRICS,
  MultiVariantHandling,
  STATS_ENGINE_LABELS,
  StatsEngine,
} from 'components/experiments-v2/types'

const directionTag = (d: MetricDirection): string => {
  if (d === 'higher-better') return '↑ higher is better'
  if (d === 'lower-better') return '↓ lower is better'
  return '— neither'
}
import './SelectMetricsStep.scss'

type SelectMetricsStepProps = {
  availableMetrics?: Metric[]
  selectedMetrics: Metric[]
  onToggleMetric: (metric: Metric) => void
  onSetRole?: (metricId: string, role: MetricRole) => void
  inclusionCriteria: InclusionCriteria
  inclusionEventName: string
  statsEngine: StatsEngine
  multiVariantHandling: MultiVariantHandling
  sequentialTesting: boolean
  onInclusionCriteriaChange: (criteria: InclusionCriteria) => void
  onInclusionEventNameChange: (eventName: string) => void
  onStatsEngineChange: (engine: StatsEngine) => void
  onMultiVariantHandlingChange: (handling: MultiVariantHandling) => void
  onSequentialTestingChange: (enabled: boolean) => void
}

const SelectMetricsStep: FC<SelectMetricsStepProps> = ({
  availableMetrics: availableMetricsProp = MOCK_METRICS,
  inclusionCriteria,
  inclusionEventName,
  multiVariantHandling,
  onInclusionCriteriaChange,
  onInclusionEventNameChange,
  onMultiVariantHandlingChange,
  onSequentialTestingChange,
  onSetRole,
  onStatsEngineChange,
  onToggleMetric,
  selectedMetrics,
  sequentialTesting,
  statsEngine,
}) => {
  const [search, setSearch] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createdMetrics, setCreatedMetrics] = useState<Metric[]>([])
  const [showAdvanced, setShowAdvanced] = useState(false)

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

  const getRoleSelector = (metric: Metric) => {
    const role = getRole(metric)
    if (!isSelected(metric) || !role || !onSetRole) return undefined
    return {
      onChange: (v: MetricRole) => onSetRole(metric.id, v),
      options: [
        { label: 'Primary', value: 'primary' as MetricRole },
        { label: 'Secondary', value: 'secondary' as MetricRole },
        { label: 'Guardrail', value: 'guardrail' as MetricRole },
      ],
      value: role,
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
              roleSelector={getRoleSelector(metric)}
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

      {/* Inclusion criteria + Advanced settings */}
      <section className='select-metrics-step__settings'>
        <h4 className='select-metrics-step__settings-title'>
          How to count exposure
        </h4>
        <span className='select-metrics-step__hint text-muted fs-small'>
          Decide which users count as exposed for the analysis. Narrowing
          inclusion to a specific event reduces dilution when many users never
          reach the surface where the flag matters.
        </span>

        <div className='select-metrics-step__field'>
          <label className='select-metrics-step__label'>
            Include people when
          </label>
          <select
            className='select-metrics-step__select'
            value={inclusionCriteria}
            onChange={(e) =>
              onInclusionCriteriaChange(e.target.value as InclusionCriteria)
            }
          >
            {(
              Object.keys(INCLUSION_CRITERIA_LABELS) as InclusionCriteria[]
            ).map((c) => (
              <option key={c} value={c}>
                {INCLUSION_CRITERIA_LABELS[c]}
              </option>
            ))}
          </select>
        </div>

        {inclusionCriteria === 'custom-event' && (
          <div className='select-metrics-step__field'>
            <label className='select-metrics-step__label'>Event name</label>
            <Input
              value={inclusionEventName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onInclusionEventNameChange(e.target.value)
              }
              placeholder='e.g. checkout_viewed'
            />
            <span className='select-metrics-step__hint text-muted fs-small'>
              Only users who triggered this event will count as exposed.
            </span>
          </div>
        )}

        <button
          type='button'
          className='select-metrics-step__advanced-toggle'
          onClick={() => setShowAdvanced((s) => !s)}
          aria-expanded={showAdvanced}
        >
          <Icon
            name={showAdvanced ? 'chevron-down' : 'chevron-right'}
            width={14}
          />
          Advanced settings
        </button>

        {showAdvanced && (
          <div className='select-metrics-step__advanced'>
            <div className='select-metrics-step__field'>
              <label className='select-metrics-step__label'>
                Statistical engine
              </label>
              <select
                className='select-metrics-step__select'
                value={statsEngine}
                onChange={(e) =>
                  onStatsEngineChange(e.target.value as StatsEngine)
                }
              >
                {(Object.keys(STATS_ENGINE_LABELS) as StatsEngine[]).map(
                  (engine) => (
                    <option key={engine} value={engine}>
                      {STATS_ENGINE_LABELS[engine]}
                      {engine === 'bayesian' ? ' (default)' : ''}
                    </option>
                  ),
                )}
              </select>
              <span className='select-metrics-step__hint text-muted fs-small'>
                {statsEngine === 'bayesian'
                  ? 'Reports "% chance variant beats control" with credible intervals. More intuitive for non-stats audiences.'
                  : 'Reports p-values and confidence intervals. Pairs with sequential testing if you need to peek before the planned end date.'}
              </span>
            </div>

            <div className='select-metrics-step__field'>
              <label className='select-metrics-step__label'>
                Multi-variant exposure handling
              </label>
              <select
                className='select-metrics-step__select'
                value={multiVariantHandling}
                onChange={(e) =>
                  onMultiVariantHandlingChange(
                    e.target.value as MultiVariantHandling,
                  )
                }
              >
                {(
                  Object.keys(
                    MULTI_VARIANT_HANDLING_LABELS,
                  ) as MultiVariantHandling[]
                ).map((h) => (
                  <option key={h} value={h}>
                    {MULTI_VARIANT_HANDLING_LABELS[h]}
                  </option>
                ))}
              </select>
              <span className='select-metrics-step__hint text-muted fs-small'>
                What to do when one user gets bucketed into multiple variants
                (device change, SDK upgrade, etc.). Excluding is the
                conservative default.
              </span>
            </div>

            {statsEngine === 'frequentist' && (
              <label className='select-metrics-step__checkbox-row'>
                <input
                  type='checkbox'
                  checked={sequentialTesting}
                  onChange={(e) => onSequentialTestingChange(e.target.checked)}
                />
                <span>
                  <strong>Sequential testing</strong>
                  <span className='select-metrics-step__hint text-muted fs-small d-block'>
                    Allow valid peeking before the experiment hits its target
                    sample size. Adjusts p-values to control false-positive
                    rate.
                  </span>
                </span>
              </label>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

SelectMetricsStep.displayName = 'SelectMetricsStep'
export default SelectMetricsStep
