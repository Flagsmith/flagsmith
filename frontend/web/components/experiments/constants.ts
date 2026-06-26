import {
  ExpectedDirection,
  Experiment,
  ExperimentMetric,
  ExperimentStatus,
  MetricDirection,
} from 'common/types/responses'

export const EXPERIMENT_STATUS_LABELS: Record<ExperimentStatus, string> = {
  completed: 'Completed',
  created: 'Draft',
  paused: 'Paused',
  running: 'Running',
}

export type FilterTab = 'all' | ExperimentStatus

export const TAB_LABELS: Record<FilterTab, string> = {
  all: 'All',
  ...EXPERIMENT_STATUS_LABELS,
}

export const TAB_ORDER: FilterTab[] = [
  'all',
  'running',
  'created',
  'paused',
  'completed',
]

// Gates draft/paused experiment states
export const ENABLE_EXPERIMENT_LIFECYCLE = false

export const VISIBLE_TAB_ORDER: FilterTab[] = ENABLE_EXPERIMENT_LIFECYCLE
  ? TAB_ORDER
  : TAB_ORDER.filter((tab) => tab !== 'created' && tab !== 'paused')

export const METRIC_DIRECTION_LABELS: Record<MetricDirection, string> = {
  down: '↓ lower is better',
  informational: 'informational',
  up: '↑ higher is better',
}

export type ExpectedDirectionOption = {
  value: ExpectedDirection
  label: string
}

export const EXPECTED_DIRECTION_OPTIONS: ExpectedDirectionOption[] = [
  { label: 'Increase', value: 'increase' },
  { label: 'Decrease', value: 'decrease' },
  { label: 'Should not increase', value: 'not_increase' },
  { label: 'Should not decrease', value: 'not_decrease' },
]

export const getExpectedDirectionLabel = (
  direction: ExpectedDirection,
): string =>
  EXPECTED_DIRECTION_OPTIONS.find((option) => option.value === direction)
    ?.label ?? direction

export const METRIC_DIRECTION_TO_EXPECTED_DIRECTION: Record<
  MetricDirection,
  ExpectedDirection | null
> = {
  down: 'decrease',
  informational: null,
  up: 'increase',
}

export const getPrimaryMetric = (
  experiment: Experiment,
): ExperimentMetric | undefined => experiment.metrics?.[0]
