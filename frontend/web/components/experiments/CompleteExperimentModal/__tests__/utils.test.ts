import {
  RolloutSelection,
  buildCompleteExperimentBody,
  getControlSelectedMessage,
  getDefaultSelection,
  getVariantChoices,
} from 'components/experiments/CompleteExperimentModal/utils'
import {
  BayesianResultsSummary,
  Experiment,
  MultivariateOption,
} from 'common/types/responses'

const experiment = {
  feature: {
    multivariate_options: [
      { id: 10, key: 'b', string_value: 'big', type: 'unicode' },
      { id: 11, key: 'c', string_value: 'huge', type: 'unicode' },
    ] as MultivariateOption[],
  },
  metrics: [{ metric: 1 }],
} as Experiment

const results = (chances: Record<string, number>): BayesianResultsSummary =>
  ({
    metrics: [
      {
        inference: Object.fromEntries(
          Object.entries(chances).map(([key, chance_to_win]) => [
            key,
            { chance_to_win },
          ]),
        ),
        metric_id: 1,
      },
    ],
  } as unknown as BayesianResultsSummary)

const NO_LEAD = 'No variant has a clear lead yet, so control is selected.'

describe('getVariantChoices', () => {
  it.each([
    ['no results', undefined, [10, 11]],
    ['ranked by chance to win', results({ b: 0.2, c: 0.7 }), [11, 10]],
  ])('%s', (_, res, optionIds) => {
    expect(getVariantChoices(experiment, res).map((c) => c.optionId)).toEqual(
      optionIds,
    )
  })
})

describe('getDefaultSelection and getControlSelectedMessage', () => {
  it.each<
    [string, BayesianResultsSummary | undefined, RolloutSelection, string]
  >([
    [
      'a variant over 95% is pre-selected',
      results({ b: 0.01, c: 0.98 }),
      { decision: 'variant', variantId: 11 },
      NO_LEAD,
    ],
    [
      'a variant at exactly 95% is not pre-selected',
      results({ b: 0.01, c: 0.95 }),
      { decision: 'control', variantId: 11 },
      NO_LEAD,
    ],
    [
      'a variant ahead at 70% is not pre-selected',
      results({ b: 0.2, c: 0.7 }),
      { decision: 'control', variantId: 11 },
      NO_LEAD,
    ],
    [
      'control wins once every variant is under 5%',
      results({ b: 0.03, c: 0.02 }),
      { decision: 'control', variantId: 10 },
      'Control is ahead, so it is selected.',
    ],
    [
      'control ahead with a variant at exactly 5% has not won yet',
      results({ b: 0.05, c: 0.02 }),
      { decision: 'control', variantId: 10 },
      NO_LEAD,
    ],
    ['no results', undefined, { decision: 'control', variantId: 10 }, NO_LEAD],
  ])('%s', (_, res, selection, message) => {
    const choices = getVariantChoices(experiment, res)
    expect(getDefaultSelection(experiment, choices, res)).toEqual(selection)
    expect(getControlSelectedMessage(experiment, res)).toBe(message)
  })
})

describe('getDefaultSelection with many variants', () => {
  it('selects control when every one of twenty variants is under 5%', () => {
    // Given
    const keys = Array.from({ length: 20 }, (_, i) => `v${i + 1}`)
    const options: MultivariateOption[] = keys.map((key, i) => ({
      boolean_value: undefined,
      default_percentage_allocation: 5,
      id: 100 + i,
      integer_value: undefined,
      key,
      string_value: key,
      type: 'unicode',
      uuid: key,
    }))
    const manyVariants: Experiment = {
      ...experiment,
      feature: { ...experiment.feature, multivariate_options: options },
    }
    const res = results(Object.fromEntries(keys.map((key) => [key, 0.049])))
    const choices = getVariantChoices(manyVariants, res)

    // When
    const selection = getDefaultSelection(manyVariants, choices, res)

    // Then
    expect(selection).toEqual({ decision: 'control', variantId: 100 })
    expect(getControlSelectedMessage(manyVariants, res)).toBe(
      'Control is ahead, so it is selected.',
    )
  })
})

describe('buildCompleteExperimentBody', () => {
  it.each<[RolloutSelection, object]>([
    [{ decision: 'control', variantId: 10 }, { rollout_decision: 'control' }],
    [
      { decision: 'variant', variantId: 10 },
      { rollout_decision: 'variant', rollout_variant: 10 },
    ],
  ])('%o', (selection, expected) => {
    expect(buildCompleteExperimentBody(selection)).toEqual(expected)
  })
})
