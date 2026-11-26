import {
  BayesianResultsSummary,
  Experiment,
  ExperimentRolloutDecision,
} from 'common/types/responses'
import { CompleteExperimentBody } from 'common/types/requests'
import { getPrimaryMetric } from 'components/experiments/constants'
import {
  VariantIdentity,
  getConclusiveWinner,
  getMetricResult,
  getVariantIdentities,
} from 'components/experiments/results/derive'

export type VariantChoice = VariantIdentity & {
  optionId: number
  chanceToWin: number | null
}

export type RolloutSelection = {
  decision: ExperimentRolloutDecision
  variantId: number | null
}

const getPrimaryMetricResult = (
  experiment: Experiment,
  results?: BayesianResultsSummary,
) => {
  const metric = getPrimaryMetric(experiment)
  if (!metric || !results) return undefined
  return getMetricResult(results, metric.metric)
}

export const getVariantChoices = (
  experiment: Experiment,
  results?: BayesianResultsSummary,
): VariantChoice[] => {
  const metricResult = getPrimaryMetricResult(experiment, results)
  const options = experiment.feature.multivariate_options ?? []
  const choices = getVariantIdentities(experiment.feature)
    .filter((v) => !v.isControl)
    .map((v, i) => ({
      ...v,
      chanceToWin: metricResult?.inference[v.key]?.chance_to_win ?? null,
      optionId: options[i].id,
    }))
  // Array.prototype.sort is stable, so unranked variants keep flag order.
  return choices.sort((a, b) => (b.chanceToWin ?? -1) - (a.chanceToWin ?? -1))
}

const getWinner = (
  experiment: Experiment,
  results?: BayesianResultsSummary,
) => {
  const metricResult = getPrimaryMetricResult(experiment, results)
  return metricResult
    ? getConclusiveWinner(
        metricResult,
        getVariantIdentities(experiment.feature),
      )
    : null
}

export const getDefaultSelection = (
  experiment: Experiment,
  choices: VariantChoice[],
  results?: BayesianResultsSummary,
): RolloutSelection => {
  const winner = getWinner(experiment, results)
  const leader = winner?.isControl
    ? undefined
    : choices.find((c) => c.key === winner?.key)
  return leader
    ? { decision: 'variant', variantId: leader.optionId }
    : { decision: 'control', variantId: choices[0]?.optionId ?? null }
}

export const getControlSelectedMessage = (
  experiment: Experiment,
  results?: BayesianResultsSummary,
): string =>
  getWinner(experiment, results)?.isControl
    ? 'Control is ahead, so it is selected.'
    : 'No variant has a clear lead yet, so control is selected.'

export const getServedVariant = (
  selection: RolloutSelection,
  control: VariantIdentity,
  choices: VariantChoice[],
): VariantIdentity | null => {
  if (selection.decision === 'disable') return null
  if (selection.decision === 'control') return control
  return choices.find((c) => c.optionId === selection.variantId) ?? null
}

export const buildCompleteExperimentBody = (
  selection: RolloutSelection,
): CompleteExperimentBody =>
  selection.decision === 'variant' && selection.variantId !== null
    ? { rollout_decision: 'variant', rollout_variant: selection.variantId }
    : { rollout_decision: selection.decision }
