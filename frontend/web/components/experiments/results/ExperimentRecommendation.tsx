import { FC, useMemo } from 'react'
import Icon from 'components/icons/Icon'
import { colorTextSuccess } from 'common/theme/tokens'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import { deriveSummary } from './ExperimentSummaryScorecard'
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

  return (
    <div className='alert alert-success experiment-recommendation mb-3'>
      <div className='d-flex align-items-center gap-2 mb-2'>
        <Icon name='checkmark-circle' width={20} fill={colorTextSuccess} />
        <span className='text-success fw-semibold'>
          {summary.chanceToBest} Winner Probability Confirmed
        </span>
      </div>
      <div>
        <VariantName name={summary.winnerName} colour={summary.winnerColour} />{' '}
        is outperforming{' '}
        <VariantName name='Control' colour={summary.controlColour} /> by{' '}
        {summary.liftVsControl} with {summary.chanceToBest} probability of being
        the best variant.
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
