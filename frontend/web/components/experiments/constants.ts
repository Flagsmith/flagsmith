import { ExperimentStatus } from 'common/types/responses'

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
