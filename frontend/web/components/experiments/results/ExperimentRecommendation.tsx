import { FC, useMemo } from 'react'
import Banner from 'components/base/Banner'
import Icon from 'components/icons/Icon'
import { colorIconSuccess, colorIconWarning } from 'common/theme/tokens'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import {
  LOSING_CHANCE_THRESHOLD,
  WINNING_CHANCE_THRESHOLD,
  deriveSummary,
  formatChancePct,
} from './derive'
import VariantName from './VariantName'

type ExperimentRecommendationProps = {
  experiment: Experiment
  results?: BayesianResultsSummary
}

const ExperimentRecommendation: FC<ExperimentRecommendationProps> = ({
  experiment,
  results,
}) => {
  const summary = useMemo(
    () => (results ? deriveSummary(experiment, results) : null),
    [experiment, results],
  )

  if (!summary) return null

  if (!summary.isConclusive) {
    return (
      <Banner
        type='info'
        title='Not enough evidence yet'
        className='experiment-recommendation mb-3'
      >
        <div>
          {summary.controlWins ? (
            <>
              <VariantName name='Control' colour={summary.controlColour} /> is
              ahead with {summary.chanceToBest} probability of being the best
              arm, but no variant has fallen below a{' '}
              {formatChancePct(LOSING_CHANCE_THRESHOLD)} chance of beating it.
            </>
          ) : (
            <>
              <VariantName
                name={summary.winnerName}
                colour={summary.winnerColour}
              />{' '}
              is ahead of{' '}
              <VariantName name='Control' colour={summary.controlColour} /> by{' '}
              {summary.liftValue} with {summary.chanceToBest} probability of
              being the best variant, below the{' '}
              {formatChancePct(WINNING_CHANCE_THRESHOLD)} needed to call a
              winner.
            </>
          )}
        </div>
        {experiment.status !== 'completed' && (
          <div className='mt-2'>
            Keep the experiment running to collect more data.
          </div>
        )}
      </Banner>
    )
  }

  if (summary.controlWins) {
    return (
      <div className='alert alert-warning experiment-recommendation mb-3'>
        <div className='d-flex align-items-center gap-2 mb-2'>
          <Icon name='warning' width={20} fill={colorIconWarning} />
          <span className='text-warning fw-semibold'>
            Control is the winner
          </span>
        </div>
        <div>
          <VariantName name='Control' colour={summary.controlColour} /> has
          shown the best performance, with {summary.chanceToBest} probability of
          being the best arm. No variant has outperformed it.
        </div>
        <div className='mt-2'>
          Consider rolling out{' '}
          <VariantName name='Control' colour={summary.controlColour} /> to all
          users.
        </div>
      </div>
    )
  }

  return (
    <div className='alert alert-success experiment-recommendation mb-3'>
      <div className='d-flex align-items-center gap-2 mb-2'>
        <Icon name='checkmark-circle' width={20} fill={colorIconSuccess} />
        <span className='text-success fw-semibold'>
          {summary.chanceToBest} Winner Probability Confirmed
        </span>
      </div>
      <div>
        <VariantName name={summary.winnerName} colour={summary.winnerColour} />{' '}
        is outperforming{' '}
        <VariantName name='Control' colour={summary.controlColour} /> by{' '}
        {summary.liftValue} with {summary.chanceToBest} probability of being the
        best variant.
      </div>
      <div className='mt-2'>
        Consider rolling out{' '}
        <VariantName name={summary.winnerName} colour={summary.winnerColour} />{' '}
        to all users.
      </div>
    </div>
  )
}

export default ExperimentRecommendation
