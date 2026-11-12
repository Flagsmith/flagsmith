import { Metric } from 'common/types/responses'
import {
  buildMetricPayload,
  canSubmitMetric,
  DEFAULT_METRIC_DEFINITION_VERSION,
  DEFAULT_METRIC_FORM_STATE,
  getMetricAggregationLabel,
  getMetricSubline,
  getMetricUsageLabel,
  metricToFormState,
  MetricFormState,
} from 'components/experiments/CreateMetricForm/utils'

const buildMetric = (overrides: Partial<Metric> = {}): Metric => ({
  aggregation: 'occurrence',
  created_at: '2026-01-01T00:00:00Z',
  definition: { event: 'checkout_completed', version: 1 },
  description: 'Percentage of users completing checkout',
  direction: 'up',
  experiments: [],
  id: 1,
  name: 'Checkout Conversion Rate',
  updated_at: '2026-01-01T00:00:00Z',
  ...overrides,
})

describe('canSubmitMetric', () => {
  it('returns false when the name is empty', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: 'checkout_completed',
      name: '   ',
    }

    expect(canSubmitMetric(state)).toBe(false)
  })

  it('returns false when the event is empty', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: '',
      name: 'Signup completion',
    }

    expect(canSubmitMetric(state)).toBe(false)
  })

  it('returns true when both name and event are present', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: 'checkout_completed',
      name: 'Signup completion',
    }

    expect(canSubmitMetric(state)).toBe(true)
  })
})

describe('buildMetricPayload', () => {
  it('trims fields and maps state to the create payload', () => {
    const state: MetricFormState = {
      aggregation: 'count',
      description: '  Purchases made  ',
      direction: 'down',
      event: '  checkout_completed  ',
      name: '  Purchases  ',
    }

    expect(buildMetricPayload(state, 1)).toEqual({
      aggregation: 'count',
      definition: { event: 'checkout_completed', version: 1 },
      description: 'Purchases made',
      direction: 'down',
      name: 'Purchases',
    })
  })

  it('stamps the definition with the provided version', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: 'checkout_completed',
      name: 'Purchases',
    }

    expect(buildMetricPayload(state, 2).definition).toEqual({
      event: 'checkout_completed',
      version: 2,
    })
  })

  it('falls back to the default version when none is given', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: 'checkout_completed',
      name: 'Purchases',
    }

    expect(buildMetricPayload(state).definition.version).toBe(
      DEFAULT_METRIC_DEFINITION_VERSION,
    )
  })
})

describe('DEFAULT_METRIC_FORM_STATE', () => {
  it('defaults to an occurrence metric where higher is better', () => {
    expect(DEFAULT_METRIC_FORM_STATE.aggregation).toBe('occurrence')
    expect(DEFAULT_METRIC_FORM_STATE.direction).toBe('up')
  })
})

describe('getMetricAggregationLabel', () => {
  it('maps each aggregation to its human label', () => {
    expect(getMetricAggregationLabel('occurrence')).toBe('Occurrence')
    expect(getMetricAggregationLabel('count')).toBe('Count')
    expect(getMetricAggregationLabel('sum')).toBe('Sum')
    expect(getMetricAggregationLabel('mean')).toBe('Mean')
  })
})

describe('getMetricSubline', () => {
  it('combines the aggregation label and event name', () => {
    const metric = buildMetric({
      aggregation: 'count',
      definition: { event: 'checkout_completed', version: 1 },
    })

    expect(getMetricSubline(metric)).toBe('Count · checkout_completed')
  })
})

describe('getMetricUsageLabel', () => {
  it('reads "Not in use" when no experiments use the metric', () => {
    expect(getMetricUsageLabel(0)).toBe('Not in use')
  })

  it('uses the singular form for a single experiment', () => {
    expect(getMetricUsageLabel(1)).toBe('1 experiment')
  })

  it('uses the plural form for multiple experiments', () => {
    expect(getMetricUsageLabel(3)).toBe('3 experiments')
  })
})

describe('metricToFormState', () => {
  it('maps a metric to editable form state', () => {
    const metric = buildMetric({
      aggregation: 'sum',
      definition: { event: 'purchase', version: 1 },
      description: 'Total revenue',
      direction: 'down',
      name: 'Revenue',
    })

    expect(metricToFormState(metric)).toEqual({
      aggregation: 'sum',
      description: 'Total revenue',
      direction: 'down',
      event: 'purchase',
      name: 'Revenue',
    })
  })
})
