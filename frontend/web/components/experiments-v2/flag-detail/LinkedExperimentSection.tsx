import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import StatusBadge from 'components/experiments-v2/shared/StatusBadge'
import { LinkedExperiment } from 'components/experiments-v2/types'
import './LinkedExperimentSection.scss'

type LinkedExperimentSectionProps = {
  experiment?: LinkedExperiment | null
  onCreateExperiment?: () => void
  onViewResults?: () => void
}

const LinkedExperimentSection: FC<LinkedExperimentSectionProps> = ({
  experiment,
  onCreateExperiment,
  onViewResults,
}) => {
  const progressPercent = experiment
    ? Math.round((experiment.sampleProgress / experiment.sampleTarget) * 100)
    : 0

  return (
    <div className='linked-experiment-section'>
      <div className='linked-experiment-section__header'>
        <span className='linked-experiment-section__title'>
          Linked Experiment
        </span>
        {experiment && (
          <Button
            theme='primary'
            size='xSmall'
            iconLeft='open-external-link'
            iconSize={14}
            onClick={onViewResults}
          >
            View Results
          </Button>
        )}
      </div>

      {experiment ? (
        <div className='linked-experiment-section__card'>
          <div className='linked-experiment-section__card-top'>
            <span className='linked-experiment-section__card-name'>
              {experiment.name}
            </span>
            <StatusBadge status={experiment.status} />
          </div>

          <div className='linked-experiment-section__details'>
            <div className='linked-experiment-section__detail-row'>
              <Icon name='pie-chart' width={14} />
              <span className='linked-experiment-section__detail-label'>
                Primary Metric:
              </span>
              <span className='linked-experiment-section__detail-value'>
                {experiment.primaryMetric}
              </span>
            </div>
            <div className='linked-experiment-section__detail-row'>
              <Icon name='clock' width={14} />
              <span className='linked-experiment-section__detail-label'>
                Running Since:
              </span>
              <span className='linked-experiment-section__detail-value'>
                {experiment.runningSince}
              </span>
            </div>
            <div className='linked-experiment-section__detail-row'>
              <Icon name='people' width={14} />
              <span className='linked-experiment-section__detail-label'>
                Traffic:
              </span>
              <span className='linked-experiment-section__detail-value'>
                {experiment.trafficSplit}
              </span>
            </div>
          </div>

          <div className='linked-experiment-section__progress'>
            <div className='linked-experiment-section__progress-header'>
              <span className='linked-experiment-section__progress-label'>
                Sample Progress
              </span>
              <span className='linked-experiment-section__progress-value'>
                {progressPercent}% ({experiment.sampleProgress.toLocaleString()}{' '}
                / {experiment.sampleTarget.toLocaleString()})
              </span>
            </div>
            <div className='linked-experiment-section__progress-track'>
              <div
                className='linked-experiment-section__progress-fill'
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>
      ) : (
        <div className='linked-experiment-section__empty'>
          <Icon name='flask' width={40} />
          <span className='linked-experiment-section__empty-title'>
            No experiment linked
          </span>
          <span className='linked-experiment-section__empty-desc'>
            Create an experiment to test variations of this feature flag and
            measure their impact on your key metrics.
          </span>
          <Button theme='primary' iconLeft='plus' onClick={onCreateExperiment}>
            Create Experiment
          </Button>
        </div>
      )}
    </div>
  )
}

LinkedExperimentSection.displayName = 'LinkedExperimentSection'
export default LinkedExperimentSection
