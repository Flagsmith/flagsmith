import { Req } from 'common/types/requests'
import {
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
  filter: string
}

export const DEFAULT_METRIC_FORM_STATE: MetricFormState = {
  aggregation: 'occurrence',
  description: '',
  direction: 'increase',
  event: '',
  filter: '',
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
  { label: 'Higher is better', value: 'increase' },
  { label: 'Lower is better', value: 'decrease' },
  { label: 'Neither — informational only', value: 'informational' },
]

export const canSubmitMetric = (state: MetricFormState): boolean =>
  state.name.trim().length > 0 && state.event.trim().length > 0

export const buildMetricPayload = (
  state: MetricFormState,
): Req['createMetric']['body'] => {
  const definition: MetricDefinition = { event: state.event.trim() }
  const filter = state.filter.trim()
  if (filter) {
    definition.filter = filter
  }
  return {
    aggregation: state.aggregation,
    definition,
    description: state.description.trim(),
    direction: state.direction,
    name: state.name.trim(),
  }
}
