import { FC } from 'react'
import SegmentsIcon from 'components/svg/SegmentsIcon'
import FeatureValue from 'components/feature-summary/FeatureValue'
import { FlagsmithValue } from 'common/types/responses'

type SegmentOverrideDescriptionType = {
  showEnabledOverride: boolean
  showValueOverride: boolean
  controlEnabled: boolean
  controlValue: FlagsmithValue
  level: 'segment' | 'identity'
}

const SegmentOverrideDescription: FC<SegmentOverrideDescriptionType> = ({
  controlEnabled,
  controlValue,
  level,
  showEnabledOverride,
  showValueOverride,
}) => {
  return (
    <>
      {showEnabledOverride && (
        <div className='list-item-subtitle'>
          <Row>
            <Flex>
              <span className='list-item-subtitle d-flex text-primary align-items-center'>
                <SegmentsIcon className='me-1' width={16} fill='#6837fc' />
                {`This flag is being overridden by ${
                  level === 'segment' ? 'this' : 'a'
                } segment and would normally be`}
                <div className='ph-1 ml-1 mr-1 fw-semibold'>
                  {controlEnabled ? 'on' : 'off'}
                </div>{' '}
                {level === 'identity' ? 'for this user' : ''}
              </span>
            </Flex>
          </Row>
        </div>
      )}
      {showValueOverride && (
        <span className='d-flex list-item-subtitle text-primary align-items-center'>
          <SegmentsIcon className='me-1' width={16} fill='#6837fc' />
          {`This feature is being overridden by a segment and would normally be`}
          <FeatureValue
            className='ml-1 chip--xs'
            includeEmpty
            value={`${controlValue}`}
          />{' '}
          {level === 'identity' ? 'for this user' : ''}
        </span>
      )}
    </>
  )
}

export default SegmentOverrideDescription
