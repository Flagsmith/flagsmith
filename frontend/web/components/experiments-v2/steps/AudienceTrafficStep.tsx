import React, { FC } from 'react'
import SearchableSelect from 'components/base/select/SearchableSelect'
import Icon from 'components/icons/Icon'
import { OptionType } from 'components/base/select/SearchableSelect'
import { AudienceConfig, MOCK_SEGMENTS } from 'components/experiments-v2/types'
import './AudienceTrafficStep.scss'

type AudienceTrafficStepProps = {
  audience: AudienceConfig
  onChange: (audience: AudienceConfig) => void
}

const AudienceTrafficStep: FC<AudienceTrafficStepProps> = ({
  audience,
  onChange,
}) => {
  return (
    <div className='audience-traffic-step'>
      <div className='audience-traffic-step__field'>
        <label className='audience-traffic-step__label'>Segments</label>
        <SearchableSelect
          value={audience.segmentId}
          onChange={(opt: OptionType) => {
            onChange({ ...audience, segmentId: opt.value })
          }}
          options={MOCK_SEGMENTS}
          placeholder='Select a segment...'
        />
      </div>

      <div className='audience-traffic-step__field'>
        <label className='audience-traffic-step__label'>
          Experiment Enrollment
        </label>
        <div className='audience-traffic-step__slider-row'>
          <input
            type='range'
            min={10}
            max={100}
            step={5}
            value={audience.trafficPercentage}
            onChange={(e) =>
              onChange({
                ...audience,
                trafficPercentage: Number(e.target.value),
              })
            }
            className='audience-traffic-step__slider'
          />
          <span className='audience-traffic-step__percentage'>
            {audience.trafficPercentage}%
          </span>
        </div>
        <div className='audience-traffic-step__split-breakdown'>
          <div className='audience-traffic-step__split-item'>
            <span className='audience-traffic-step__split-label'>Control</span>
            <span className='audience-traffic-step__split-value'>
              {100 - audience.trafficPercentage}% — current flag value
            </span>
          </div>
          <div className='audience-traffic-step__split-item'>
            <span className='audience-traffic-step__split-label'>
              Experiment
            </span>
            <span className='audience-traffic-step__split-value'>
              {audience.trafficPercentage}% — randomly assigned to variations
            </span>
          </div>
        </div>
      </div>

      <div className='audience-traffic-step__sample-estimate'>
        <Icon name='people' width={20} />
        <span>
          ~6,200 users per variation &middot; Est. 14 days to significance
        </span>
      </div>
    </div>
  )
}

AudienceTrafficStep.displayName = 'AudienceTrafficStep'
export default AudienceTrafficStep
