import {
  buildMetricPayload,
  canSubmitMetric,
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
      direction: 'decrease',
      event: '  checkout_completed  ',
      filter: '',
      name: '  Purchases  ',
    }

    expect(buildMetricPayload(state)).toEqual({
      aggregation: 'count',
      definition: { event: 'checkout_completed' },
      description: 'Purchases made',
      direction: 'decrease',
      name: 'Purchases',
    })
  })

  it('includes the trimmed filter in the definition when provided', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: 'checkout_completed',
      filter: "  status = 'complete'  ",
      name: 'Purchases',
    }

    expect(buildMetricPayload(state).definition).toEqual({
      event: 'checkout_completed',
      filter: "status = 'complete'",
    })
  })

  it('omits the filter from the definition when blank', () => {
    const state: MetricFormState = {
      ...DEFAULT_METRIC_FORM_STATE,
      event: 'checkout_completed',
      filter: '   ',
      name: 'Purchases',
    }

    expect(buildMetricPayload(state).definition).toEqual({
      event: 'checkout_completed',
    })
  })
})

describe('DEFAULT_METRIC_FORM_STATE', () => {
  it('defaults to an occurrence metric where higher is better', () => {
    expect(DEFAULT_METRIC_FORM_STATE.aggregation).toBe('occurrence')
    expect(DEFAULT_METRIC_FORM_STATE.direction).toBe('increase')
  })
})
