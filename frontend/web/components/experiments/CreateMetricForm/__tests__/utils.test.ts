import {
  buildMetricPayload,
  canSubmitMetric,
  DEFAULT_METRIC_DEFINITION_VERSION,
  DEFAULT_METRIC_FORM_STATE,
  MetricFormState,
} from 'components/experiments/CreateMetricForm/utils'

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
