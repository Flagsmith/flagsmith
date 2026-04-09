import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
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

const TYPE_CONFIG: Record<string, { icon: string; label: string }> = {
  ab_test: { icon: 'bar-chart', label: 'A/B Test' },
  feature_flag: { icon: 'features', label: 'Feature Flag' },
  multivariate: { icon: 'layers', label: 'Multivariate' },
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
  const typeConfig = wizardState.details.type
    ? TYPE_CONFIG[wizardState.details.type]
    : null
  const splitPerVariation = Math.round(
    wizardState.audience.trafficPercentage /
      Math.max(wizardState.variations.length, 1),
  )

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
        {wizardState.details.hypothesis && (
          <div className='review-launch-step__row review-launch-step__row--block'>
            <span className='review-launch-step__label'>Hypothesis</span>
            <span className='review-launch-step__hypothesis'>
              {wizardState.details.hypothesis}
            </span>
          </div>
        )}
        {typeConfig && (
          <div className='review-launch-step__row'>
            <span className='review-launch-step__label'>Type</span>
            <span className='review-launch-step__type-badge'>
              <Icon name={typeConfig.icon} width={14} />
              {typeConfig.label}
            </span>
          </div>
        )}
      </div>

      {/* Step 2: Metrics */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Metrics ({wizardState.metrics.length})
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(1)}>
            Edit
          </Button>
        </div>
        {wizardState.metrics.length > 0 ? (
          wizardState.metrics.map((m) => (
            <div key={m.id} className='review-launch-step__metric-row'>
              <div className='review-launch-step__metric-info'>
                <span className='review-launch-step__metric-name'>
                  {m.name}
                </span>
                <span className='review-launch-step__metric-desc'>
                  {m.description}
                </span>
              </div>
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
        <div className='review-launch-step__variations'>
          {wizardState.variations.map((v) => (
            <div key={v.id} className='review-launch-step__variation'>
              <span
                className='review-launch-step__variation-dot'
                style={{ background: v.colour }}
              />
              <span className='review-launch-step__variation-name'>
                {v.name}
              </span>
              <span className='review-launch-step__variation-value'>
                {v.value}
              </span>
            </div>
          ))}
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
          <span className='review-launch-step__label'>Total Traffic</span>
          <span className='review-launch-step__value'>
            {wizardState.audience.trafficPercentage}%
          </span>
        </div>
        <div className='review-launch-step__traffic-split'>
          <div className='review-launch-step__traffic-bar'>
            {wizardState.variations.map((v) => (
              <div
                key={v.id}
                className='review-launch-step__traffic-segment'
                style={{
                  background: v.colour,
                  width: `${splitPerVariation}%`,
                }}
              />
            ))}
          </div>
          <div className='review-launch-step__traffic-labels'>
            {wizardState.variations.map((v) => (
              <span key={v.id} className='review-launch-step__traffic-label'>
                <span
                  className='review-launch-step__traffic-label-dot'
                  style={{ background: v.colour }}
                />
                {v.name}: {splitPerVariation}%
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

ReviewLaunchStep.displayName = 'ReviewLaunchStep'
export default ReviewLaunchStep
