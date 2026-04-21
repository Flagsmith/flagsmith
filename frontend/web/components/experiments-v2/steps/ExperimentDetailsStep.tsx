import React, { FC } from 'react'
import Input from 'components/base/forms/Input'
import { ExperimentDetails } from 'components/experiments-v2/types'
import './ExperimentDetailsStep.scss'

type ExperimentDetailsStepProps = {
  details: ExperimentDetails
  onChange: (details: ExperimentDetails) => void
}

const ExperimentDetailsStep: FC<ExperimentDetailsStepProps> = ({
  details,
  onChange,
}) => {
  return (
    <div className='experiment-details-step'>
      <div className='experiment-details-step__field'>
        <label className='experiment-details-step__label'>
          Experiment Name{' '}
          <span className='experiment-details-step__required'>*</span>
        </label>
        <Input
          value={details.name}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onChange({ ...details, name: e.target.value })
          }
          placeholder='e.g. Checkout Flow Redesign'
        />
      </div>

      <div className='experiment-details-step__field'>
        <label className='experiment-details-step__label'>
          Hypothesis{' '}
          <span className='experiment-details-step__required'>*</span>
        </label>
        <textarea
          className='experiment-details-step__textarea'
          value={details.hypothesis}
          onChange={(e) => onChange({ ...details, hypothesis: e.target.value })}
          placeholder='e.g. Switching to a one-click checkout will increase completion rate by at least 10% within 30 days.'
          rows={3}
        />
        <span className='experiment-details-step__hint text-muted fs-small'>
          A good hypothesis names the change, the metric, the expected
          magnitude, and the timeframe.
        </span>
      </div>

      <div className='experiment-details-step__date-row'>
        <div className='experiment-details-step__field'>
          <label className='experiment-details-step__label'>Start date</label>
          <Input
            type='date'
            value={details.startDate}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onChange({ ...details, startDate: e.target.value })
            }
          />
        </div>
        <div className='experiment-details-step__field'>
          <label className='experiment-details-step__label'>End date</label>
          <Input
            type='date'
            value={details.endDate}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onChange({ ...details, endDate: e.target.value })
            }
          />
        </div>
      </div>
    </div>
  )
}

ExperimentDetailsStep.displayName = 'ExperimentDetailsStep'
export default ExperimentDetailsStep
