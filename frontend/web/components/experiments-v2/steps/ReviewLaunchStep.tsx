import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import {
  CONTROL_ARM_ID,
  CONTROL_COLOUR,
  ExperimentWizardState,
  MOCK_FLAGS,
  MOCK_SEGMENTS,
  Variation,
} from 'components/experiments-v2/types'
import './ReviewLaunchStep.scss'

type ReviewLaunchStepProps = {
  wizardState: ExperimentWizardState
  onEditStep: (step: number) => void
}

const ReviewLaunchStep: FC<ReviewLaunchStepProps> = ({
  onEditStep,
  wizardState,
}) => {
  const flagLabel =
    MOCK_FLAGS.find((f) => f.value === wizardState.featureFlagId)?.label ?? '—'
  const segmentLabel =
    MOCK_SEGMENTS.find((s) => s.value === wizardState.segmentTraffic.segmentId)
      ?.label ?? '—'

  const controlArm: Variation = {
    colour: CONTROL_COLOUR,
    description: "Flag's base value — the baseline for comparison",
    id: CONTROL_ARM_ID,
    name: 'Control',
    value: wizardState.controlValue,
  }
  const arms: Variation[] = [controlArm, ...wizardState.variations]
  const weightFor = (armId: string) =>
    wizardState.segmentTraffic.weights.find((w) => w.armId === armId)?.weight ??
    0

  return (
    <div className='review-launch-step'>
      {/* Step 1: Flag & Variations */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Flag & Variations
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(0)}>
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
          {arms.map((v) => (
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

      {/* Step 2: Experiment Details */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Experiment Details
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(1)}>
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
        {(wizardState.details.startDate || wizardState.details.endDate) && (
          <div className='review-launch-step__row'>
            <span className='review-launch-step__label'>Dates</span>
            <span className='review-launch-step__value'>
              {wizardState.details.startDate || '—'} →{' '}
              {wizardState.details.endDate || '—'}
            </span>
          </div>
        )}
      </div>

      {/* Step 3: Metrics */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Metrics ({wizardState.metrics.length})
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(2)}>
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

      {/* Step 4: Segments & Traffic */}
      <div className='review-launch-step__section'>
        <div className='review-launch-step__section-header'>
          <span className='review-launch-step__section-title'>
            Segments & Traffic
          </span>
          <Button theme='text' size='xSmall' onClick={() => onEditStep(3)}>
            Edit
          </Button>
        </div>
        <div className='review-launch-step__row'>
          <span className='review-launch-step__label'>Segment</span>
          <span className='review-launch-step__value'>{segmentLabel}</span>
        </div>
        <div className='review-launch-step__traffic-split'>
          <div className='review-launch-step__traffic-bar'>
            {arms.map((v) => {
              const w = weightFor(v.id)
              if (w === 0) return null
              return (
                <div
                  key={v.id}
                  className='review-launch-step__traffic-segment'
                  style={{
                    background: v.colour,
                    width: `${w}%`,
                  }}
                />
              )
            })}
          </div>
          <div className='review-launch-step__traffic-labels'>
            {arms.map((v) => (
              <span key={v.id} className='review-launch-step__traffic-label'>
                <span
                  className='review-launch-step__traffic-label-dot'
                  style={{ background: v.colour }}
                />
                {v.name}: {weightFor(v.id)}%
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
