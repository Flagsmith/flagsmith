import { FC, useMemo } from 'react'
import Icon from 'components/icons/Icon'
import InfoMessage from 'components/InfoMessage'
import { colorTextSuccess } from 'common/theme/tokens'
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

type SummaryStats = {
  winnerName: string
  chanceToBest: string
  liftVsControl: string
  liftFavourable: boolean
}

const deriveSummary = (
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

  return {
    chanceToBest: `${Math.round(winner.chanceToWin * 100)}%`,
    liftFavourable: isLiftFavourable(
      winner.inference.lift,
      metric.expected_direction,
    ),
    liftVsControl: formatLiftPct(winner.inference.lift),
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
      {summary ? (
        <div className='alert alert-success mb-3'>
          <div className='d-flex align-items-center gap-2 mb-1'>
            <Icon name='checkmark-circle' width={20} fill={colorTextSuccess} />
            <span className='text-success fw-normal'>Recommendation</span>
          </div>
          <div>
            {summary.winnerName} is outperforming Control with{' '}
            {summary.chanceToBest} probability of being the best variant.
          </div>
        </div>
      ) : (
        hasResults && (
          <InfoMessage title='Collecting data'>
            The experiment is still gathering data. Results will appear once
            there is enough traffic for statistically meaningful analysis.
          </InfoMessage>
        )
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
