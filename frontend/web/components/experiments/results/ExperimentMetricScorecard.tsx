import { FC, useMemo } from 'react'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import {
  computeAxisRange,
  computeLiftRange,
  getMetricResult,
  getVariantIdentities,
  getWinningVariant,
} from './derive'
import ExperimentResultsAxisChart from './ExperimentResultsAxisChart'
import ExperimentResultsScorecardTable from './ExperimentResultsScorecardTable'
import './results.scss'

type ExperimentMetricScorecardProps = {
  experiment: Experiment
  results?: BayesianResultsSummary
}

const ExperimentMetricScorecard: FC<ExperimentMetricScorecardProps> = ({
  experiment,
  results,
}) => {
  const metric = getPrimaryMetric(experiment)
  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )
  const metricResult = useMemo(
    () =>
      metric && results ? getMetricResult(results, metric.metric) : undefined,
    [metric, results],
  )
  const srmBroken =
    !!results && results.srm_p_value !== null && results.srm_p_value < 0.001

  const winner = useMemo(
    () => (metricResult ? getWinningVariant(metricResult, identities) : null),
    [metricResult, identities],
  )

  const axisRange = useMemo(
    () => computeAxisRange(identities, metricResult),
    [identities, metricResult],
  )

  const liftRange = useMemo(
    () => computeLiftRange(identities, metricResult),
    [identities, metricResult],
  )

  if (!metric) return null

  return (
    <>
      {metricResult && (
        <ExperimentResultsAxisChart
          identities={identities}
          metricName={metric.metric_name}
          metricResult={metricResult}
          range={axisRange}
        />
      )}

      <ExperimentResultsScorecardTable
        identities={identities}
        liftRange={liftRange}
        metric={metric}
        metricResult={metricResult}
        srmBroken={srmBroken}
        winnerKey={winner?.key}
      />
    </>
  )
}

export default ExperimentMetricScorecard
