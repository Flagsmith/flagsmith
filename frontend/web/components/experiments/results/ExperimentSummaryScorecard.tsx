import { FC, useMemo } from 'react'
import InfoMessage from 'components/InfoMessage'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import { deriveSummary } from './derive'
import StatCard from './StatCard'

type ExperimentSummaryScorecardProps = {
  usersEnrolled: number | null
  experiment?: Experiment
  results?: BayesianResultsSummary
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

  let liftClassName: string | undefined
  if (summary && !summary.controlWins) {
    liftClassName = summary.liftFavourable ? 'text-success' : 'text-danger'
  }

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
                <span
                  className={summary.controlWins ? undefined : 'text-success'}
                >
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
                <span className={liftClassName}>{summary.liftVsControl}</span>
              ) : undefined
            }
          />
        </div>
      </div>
    </>
  )
}

export default ExperimentSummaryScorecard
