import React, { FC } from 'react'
import SearchableSelect from 'components/base/select/SearchableSelect'
import Icon from 'components/icons/Icon'
import TrafficSplitBar from 'components/experiments-v2/shared/TrafficSplitBar'
import { OptionType } from 'components/base/select/SearchableSelect'
import {
  AudienceConfig,
  MOCK_SEGMENTS,
  Variation,
} from 'components/experiments-v2/types'
import './AudienceTrafficStep.scss'

type AudienceTrafficStepProps = {
  audience: AudienceConfig
  variations: Variation[]
  onChange: (audience: AudienceConfig) => void
}

const AudienceTrafficStep: FC<AudienceTrafficStepProps> = ({
  audience,
  onChange,
  variations,
}) => {
  const splitPerVariation = Math.round(
    audience.trafficPercentage / Math.max(variations.length, 1),
  )

  const splits = variations.map((v) => ({
    colour: v.colour,
    name: v.name,
    percentage: splitPerVariation,
  }))

  return (
    <div className='audience-traffic-step'>
      <div className='audience-traffic-step__field'>
        <label className='audience-traffic-step__label'>Target Audience</label>
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
          Traffic Allocation
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
      </div>

      <div className='audience-traffic-step__field'>
        <label className='audience-traffic-step__label'>Traffic Split</label>
        <TrafficSplitBar splits={splits} />
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
