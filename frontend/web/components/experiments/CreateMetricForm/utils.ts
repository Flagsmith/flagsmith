import { Req } from 'common/types/requests'
import {
  Metric,
  MetricAggregation,
  MetricDefinition,
  MetricDirection,
} from 'common/types/responses'

export type MetricFormState = {
  name: string
  description: string
  aggregation: MetricAggregation
  direction: MetricDirection
  event: string
}

export const DEFAULT_METRIC_DEFINITION_VERSION = 1

export const DEFAULT_METRIC_FORM_STATE: MetricFormState = {
  aggregation: 'occurrence',
  description: '',
  direction: 'up',
  event: '',
  name: '',
}

export type MeasurementOption = {
  value: MetricAggregation
  title: string
  description: string
  example: string
}

export const MEASUREMENT_OPTIONS: MeasurementOption[] = [
  {
    description: 'Whether an event is seen at least once',
    example: 'ex: Signup completion',
    title: 'Occurrence',
    value: 'occurrence',
  },
  {
    description: 'Number of times an event occurred',
    example: 'ex: Number of purchases',
    title: 'Count',
    value: 'count',
  },
  {
    description: 'Total of a numeric value across events',
    example: 'ex: Total revenue',
    title: 'Sum',
    value: 'sum',
  },
  {
    description: 'Average of a numeric value across events',
    example: 'ex: Average order value',
    title: 'Mean',
    value: 'mean',
  },
]

export type DirectionOption = {
  value: MetricDirection
  label: string
}

export const DIRECTION_OPTIONS: DirectionOption[] = [
  { label: 'Higher is better', value: 'up' },
  { label: 'Lower is better', value: 'down' },
  { label: 'Neither — informational only', value: 'informational' },
]

export const canSubmitMetric = (state: MetricFormState): boolean =>
  state.name.trim().length > 0 && state.event.trim().length > 0

export const getMetricAggregationLabel = (
  aggregation: MetricAggregation,
): string =>
  MEASUREMENT_OPTIONS.find((option) => option.value === aggregation)?.title ??
  aggregation

export const getMetricSubline = (metric: Metric): string =>
  `${getMetricAggregationLabel(metric.aggregation)} · ${
    metric.definition.event
  }`

export const getMetricUsageLabel = (experimentCount: number): string => {
  if (experimentCount === 0) return 'Not in use'
  if (experimentCount === 1) return '1 experiment'
  return `${experimentCount} experiments`
}

export const metricToFormState = (metric: Metric): MetricFormState => ({
  aggregation: metric.aggregation,
  description: metric.description,
  direction: metric.direction,
  event: metric.definition.event,
  name: metric.name,
})

export const buildMetricPayload = (
  state: MetricFormState,
  version: number = DEFAULT_METRIC_DEFINITION_VERSION,
): Req['createMetric']['body'] => {
  const definition: MetricDefinition = { event: state.event.trim(), version }
  return {
    aggregation: state.aggregation,
    definition,
    description: state.description.trim(),
    direction: state.direction,
    name: state.name.trim(),
  }
}
