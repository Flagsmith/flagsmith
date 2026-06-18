import { FC, useMemo } from 'react'
import Icon from 'components/icons/Icon'
import InfoMessage from 'components/InfoMessage'
import {
  BayesianResultsSummary,
  Experiment,
  Inference,
} from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import { getVariantIdentities } from './derive'
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
} | null

const deriveSummary = (
  experiment: Experiment,
  results: BayesianResultsSummary,
): SummaryStats => {
  const metric = getPrimaryMetric(experiment)
  if (!metric) return null
  const metricResult = results.metrics.find(
    (m) => m.metric_id === metric.metric,
  )
  if (!metricResult) return null

  const identities = getVariantIdentities(experiment.feature)
  let best: { name: string; ctw: number; inference: Inference } | null = null

  identities.forEach((v) => {
    if (v.isControl) return
    const inf = metricResult.inference[v.key]
    if (!inf) return
    if (!best || inf.chance_to_win > best.ctw) {
      best = { ctw: inf.chance_to_win, inference: inf, name: v.name }
    }
  })

  if (!best) return null
  const winner = best as { name: string; ctw: number; inference: Inference }
  const dir = metric.expected_direction
  const favourable =
    dir === 'increase' || dir === 'not_decrease'
      ? winner.inference.lift > 0
      : winner.inference.lift < 0
  return {
    chanceToBest: `${Math.round(winner.ctw * 100)}%`,
    liftFavourable: favourable,
    liftVsControl: `${winner.inference.lift >= 0 ? '+' : ''}${(
      winner.inference.lift * 100
    ).toFixed(1)}%`,
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
            <Icon
              name='checkmark-circle'
              width={20}
              fill='var(--color-text-success)'
            />
            <span
              style={{
                color: 'var(--color-text-success)',
                fontWeight: 'var(--font-weight-regular)' as string,
              }}
            >
              Recommendation
            </span>
          </div>
          <div>
            {summary.winnerName} is outperforming Control with{' '}
            {summary.chanceToBest} probability of being the best variant.
          </div>
        </div>
      ) : (
        hasResults &&
        !summary && (
          <InfoMessage title='Collecting data'>
            The experiment is still gathering data. Results will appear once
            there is enough traffic for statistically meaningful analysis.
          </InfoMessage>
        )
      )}
      <div className='row mb-4'>
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
                <span style={{ color: 'var(--color-text-success)' }}>
                  {summary.winnerName}
                </span>
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
                  style={{
                    color: summary.liftFavourable
                      ? 'var(--color-text-success)'
                      : 'var(--color-text-danger)',
                  }}
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
