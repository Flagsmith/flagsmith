import {
  RolloutSelection,
  buildCompleteExperimentBody,
  getControlSelectedMessage,
  getDefaultSelection,
  getServedVariant,
  getVariantChoices,
} from 'components/experiments/CompleteExperimentModal/utils'
import { getVariantIdentities } from 'components/experiments/results/derive'
import {
  BayesianResultsSummary,
  Experiment,
  Inference,
  MultivariateOption,
} from 'common/types/responses'

const option = (over: Partial<MultivariateOption>): MultivariateOption => ({
  default_percentage_allocation: 0,
  id: 1,
  key: null,
  string_value: '',
  type: 'unicode',
  uuid: 'u',
  ...over,
})

const experiment: Experiment = {
  created_at: '2026-06-01T00:00:00Z',
  ended_at: null,
  feature: {
    id: 1,
    initial_value: 'off',
    multivariate_options: [
      option({ id: 10, key: 'b', string_value: 'big' }),
      option({ id: 11, key: 'c', string_value: 'huge' }),
    ],
    name: 'checkout',
    type: 'MULTIVARIATE',
  },
  hypothesis: '',
  id: 1,
  metrics: [
    {
      aggregation: 'occurrence',
      created_at: '2026-06-01T00:00:00Z',
      direction: 'up',
      expected_direction: 'increase',
      id: 1,
      metric: 1,
      metric_name: 'Signup',
    },
  ],
  name: 'exp',
  rollout_decision: null,
  rollout_variant: null,
  started_at: null,
  status: 'running',
  updated_at: '2026-06-01T00:00:00Z',
}

const inference = (chance_to_win: number): Inference => ({
  chance_to_win,
  ci_high: 0.1,
  ci_low: -0.1,
  lift: 0,
})

const results = (
  chances: Record<string, number | null>,
): BayesianResultsSummary => ({
  metrics: [
    {
      inference: Object.fromEntries(
        Object.entries(chances).map(([key, chance]) => [
          key,
          chance === null ? null : inference(chance),
        ]),
      ),
      metric_id: 1,
      variants: {},
    },
  ],
  srm_p_value: null,
})

const control = getVariantIdentities(experiment.feature)[0]

describe('getVariantChoices', () => {
  it.each([
    ['no results', undefined, ['b', 'c'], [null, null]],
    ['ranked results', results({ b: 0.2, c: 0.7 }), ['c', 'b'], [0.7, 0.2]],
    ['partial results', results({ b: null, c: 0.4 }), ['c', 'b'], [0.4, null]],
  ])('%s', (_, res, keys, chances) => {
    const choices = getVariantChoices(experiment, res)
    expect(choices.map((c) => c.key)).toEqual(keys)
    expect(choices.map((c) => c.chanceToWin)).toEqual(chances)
  })

  it('maps each variant to its multivariate option id and value', () => {
    expect(getVariantChoices(experiment)).toMatchObject([
      { name: 'b', optionId: 10, value: 'big' },
      { name: 'c', optionId: 11, value: 'huge' },
    ])
  })
})

describe('getDefaultSelection', () => {
  it.each<[string, BayesianResultsSummary | undefined, RolloutSelection]>([
    [
      'leading treatment',
      results({ b: 0.2, c: 0.7 }),
      { decision: 'variant', variantId: 11 },
    ],
    [
      'control leads',
      results({ b: 0.05, c: 0.05 }),
      { decision: 'control', variantId: 10 },
    ],
    ['no results', undefined, { decision: 'control', variantId: 10 }],
  ])('%s', (_, res, expected) => {
    const choices = getVariantChoices(experiment, res)
    expect(getDefaultSelection(experiment, choices, res)).toEqual(expected)
  })
})

describe('getControlSelectedMessage', () => {
  it.each([
    [
      'control leads',
      results({ b: 0.05, c: 0.05 }),
      'Control is ahead, so it is selected.',
    ],
    [
      'no inference',
      results({}),
      'No variant has a clear lead yet, so control is selected.',
    ],
    [
      'no results',
      undefined,
      'No variant has a clear lead yet, so control is selected.',
    ],
  ])('%s', (_, res, expected) => {
    expect(getControlSelectedMessage(experiment, res)).toBe(expected)
  })
})

describe('getServedVariant', () => {
  const choices = getVariantChoices(experiment)

  it.each<[string, RolloutSelection, string | null]>([
    ['control', { decision: 'control', variantId: 11 }, 'Control'],
    ['variant', { decision: 'variant', variantId: 11 }, 'c'],
    ['unknown variant', { decision: 'variant', variantId: 99 }, null],
    ['disable', { decision: 'disable', variantId: 11 }, null],
  ])('%s', (_, selection, expected) => {
    expect(getServedVariant(selection, control, choices)?.name ?? null).toBe(
      expected,
    )
  })
})

describe('buildCompleteExperimentBody', () => {
  it.each<[string, RolloutSelection, object]>([
    [
      'control',
      { decision: 'control', variantId: 10 },
      { rollout_decision: 'control' },
    ],
    [
      'variant',
      { decision: 'variant', variantId: 10 },
      { rollout_decision: 'variant', rollout_variant: 10 },
    ],
    [
      'disable',
      { decision: 'disable', variantId: 10 },
      { rollout_decision: 'disable' },
    ],
  ])('%s', (_, selection, expected) => {
    expect(buildCompleteExperimentBody(selection)).toEqual(expected)
  })
})
