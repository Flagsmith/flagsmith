import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import {
  ExperimentWizardState,
  MOCK_FLAGS,
  MOCK_SEGMENTS,
} from 'components/experiments-v2/types'
import './ReviewLaunchStep.scss'

type ReviewLaunchStepProps = {
  wizardState: ExperimentWizardState
  onEditStep: (step: number) => void
}

const TYPE_LABELS: Record<string, string> = {
  ab_test: 'A/B Test',
  feature_flag: 'Feature Flag',
  multivariate: 'Multivariate',
}

const ReviewLaunchStep: FC<ReviewLaunchStepProps> = ({
  onEditStep,
  wizardState,
}) => {
  const flagLabel =
    MOCK_FLAGS.find((f) => f.value === wizardState.featureFlagId)?.label ?? '—'
  const segmentLabel =
    MOCK_SEGMENTS.find((s) => s.value === wizardState.audience.segmentId)
      ?.label ?? 'All Users'

  return (
    <div className='review-launch-step'>
      {/* Step 1: Experiment Details */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Experiment Details
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(0)}>
            Edit
          </Button>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Name</span>
          <span className='review-launch-step__value'>
            {wizardState.details.name || '—'}
          </span>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Hypothesis</span>
          <span className='review-launch-step__value'>
            {wizardState.details.hypothesis || '—'}
          </span>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Type</span>
          <span className='review-launch-step__value'>
            {wizardState.details.type
              ? TYPE_LABELS[wizardState.details.type]
              : '—'}
          </span>
        </div>
      </div>

      {/* Step 2: Metrics */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>Metrics</span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(1)}>
            Edit
          </Button>
        </div>
        {wizardState.metrics.length > 0 ? (
          wizardState.metrics.map((m) => (
            <div key={m.id} className='review-launch-step__row'>
              <span className='review-launch-step__label'>{m.name}</span>
              <span
                className={`review-launch-step__badge review-launch-step__badge--${m.role}`}
              >
                {m.role}
              </span>
            </div>
          ))
        ) : (
          <span className='review-launch-step__empty'>No metrics selected</span>
        )}
      </div>

      {/* Step 3: Flag & Variations */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Flag & Variations
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(2)}>
            Edit
          </Button>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Feature Flag</span>
          <span className='review-launch-step__value review-launch-step__value--mono'>
            {flagLabel}
          </span>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Variations</span>
          <span className='review-launch-step__value'>
            {wizardState.variations.map((v) => v.name).join(', ')}
          </span>
        </div>
      </div>

      {/* Step 4: Audience & Traffic */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Audience & Traffic
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(3)}>
            Edit
          </Button>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Segment</span>
          <span className='review-launch-step__value'>{segmentLabel}</span>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Traffic</span>
          <span className='review-launch-step__value'>
            {wizardState.audience.trafficPercentage}%
          </span>
        </div>
      </div>
    </div>
  )
}

ReviewLaunchStep.displayName = 'ReviewLaunchStep'
export default ReviewLaunchStep
