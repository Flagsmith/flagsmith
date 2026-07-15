import { FC, useMemo } from 'react'
import InfoMessage from 'components/InfoMessage'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import {
  formatLiftPct,
  getMetricResult,
  getVariantIdentities,
  getWinningVariant,
  isLiftFavourable,
} from './derive'
import StatCard from './StatCard'

type ExperimentSummaryScorecardProps = {
  usersEnrolled: number | null
  experiment?: Experiment
  results?: BayesianResultsSummary
}

export type SummaryStats = {
  winnerName: string
  winnerColour: string
  controlColour: string
  chanceToBest: string
  liftVsControl: string
  liftFavourable: boolean
}

export const deriveSummary = (
  experiment: Experiment,
  results: BayesianResultsSummary,
): SummaryStats | null => {
  const metric = getPrimaryMetric(experiment)
  if (!metric) return null
  const metricResult = getMetricResult(results, metric.metric)
  if (!metricResult) return null

  const identities = getVariantIdentities(experiment.feature)
  const winner = getWinningVariant(metricResult, identities)
  if (!winner) return null

  const winnerIdentity = identities.find((v) => v.key === winner.key)
  const controlIdentity = identities.find((v) => v.isControl)

  return {
    chanceToBest: `${Math.round(winner.chanceToWin * 100)}%`,
    controlColour: controlIdentity?.colour ?? '',
    liftFavourable: isLiftFavourable(
      winner.inference.lift,
      metric.expected_direction,
    ),
    liftVsControl: formatLiftPct(winner.inference.lift),
    winnerColour: winnerIdentity?.colour ?? '',
    winnerName: winner.name,
  }
}

const ExperimentSummaryScorecard: FC<ExperimentSummaryScorecardProps> = ({
  experiment,
  results,
  usersEnrolled,
}) => {
  const summary = useMemo(
    () => (experiment && results ? deriveSummary(experiment, results) : null),
    [experiment, results],
  )
  const hasResults = !!results

  return (
    <>
      {!summary && hasResults && (
        <InfoMessage title='Collecting data'>
          The experiment is still gathering data. Results will appear once there
          is enough traffic for statistically meaningful analysis.
        </InfoMessage>
      )}
      <div className='row g-3 mb-4'>
        <div className='col-md-3'>
          <StatCard
            label='Users enrolled'
            loading={usersEnrolled === null}
            value={usersEnrolled?.toLocaleString()}
          />
        </div>
        <div className='col-md-3'>
          <StatCard
            label='Winning variation'
            loading={!hasResults}
            value={
              summary?.winnerName ? (
                <span className='text-success'>{summary.winnerName}</span>
              ) : undefined
            }
          />
        </div>
        <div className='col-md-3'>
          <StatCard
            label='Chance to be best'
            loading={!hasResults}
            value={summary?.chanceToBest}
          />
        </div>
        <div className='col-md-3'>
          <StatCard
            label='Lift vs control'
            loading={!hasResults}
            value={
              summary?.liftVsControl ? (
                <span
                  className={
                    summary.liftFavourable ? 'text-success' : 'text-danger'
                  }
                >
                  {summary.liftVsControl}
                </span>
              ) : undefined
            }
          />
        </div>
      </div>
    </>
  )
}

export default ExperimentSummaryScorecard
