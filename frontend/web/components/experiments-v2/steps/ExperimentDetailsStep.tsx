import React, { FC } from 'react'
import Input from 'components/base/forms/Input'
import { IconName } from 'components/icons/Icon'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import {
  ExperimentDetails,
  ExperimentType,
} from 'components/experiments-v2/types'
import './ExperimentDetailsStep.scss'

type ExperimentDetailsStepProps = {
  details: ExperimentDetails
  onChange: (details: ExperimentDetails) => void
}

const TYPE_CONFIG: Record<
  ExperimentType,
  { icon: IconName; title: string; description: string }
> = {
  ab_test: {
    description: 'Compare two variations',
    icon: 'bar-chart',
    title: 'A/B Test',
  },
  feature_flag: {
    description: 'Toggle feature on/off',
    icon: 'features',
    title: 'Feature Flag',
  },
  multivariate: {
    description: 'Test multiple variables',
    icon: 'layers',
    title: 'Multivariate',
  },
}

const EXPERIMENT_TYPES: ExperimentType[] = [
  'ab_test',
  'multivariate',
  'feature_flag',
]

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
          placeholder='Describe what you expect to happen...'
          rows={3}
        />
      </div>

      <div className='experiment-details-step__field'>
        <label className='experiment-details-step__label'>
          Experiment Type{' '}
          <span className='experiment-details-step__required'>*</span>
        </label>
        <div className='experiment-details-step__type-cards'>
          {EXPERIMENT_TYPES.map((type) => {
            const config = TYPE_CONFIG[type]
            return (
              <SelectableCard
                key={type}
                icon={config.icon}
                title={config.title}
                description={config.description}
                selected={details.type === type}
                onClick={() => onChange({ ...details, type })}
              />
            )
          })}
        </div>
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
