import {
  ExpectedDirection,
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

export const METRIC_DIRECTION_LABELS: Record<MetricDirection, string> = {
  down: '↓ Lower is better',
  informational: 'Informational',
  up: '↑ Higher is better',
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
