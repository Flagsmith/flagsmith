import { FC } from 'react'
import Utils from 'common/utils/utils'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'

type SegmentOverrideLimitType = {
  id: string
  maxSegmentOverride: number
}

const SegmentOverrideLimit: FC<SegmentOverrideLimitType> = ({
  id,
  maxSegmentOverridesAllowed,
}) => {
  const { data } = useGetEnvironmentQuery({ id })

  const segmentOverrideLimitAlert = Utils.calculateRemainingLimitsPercentage(
    data?.total_segment_overrides,
    maxSegmentOverridesAllowed,
  )

  return (
    <Row>
      {Utils.displayLimitAlert(
        'segment overrides',
        segmentOverrideLimitAlert.percentage,
      )}
    </Row>
  )
}

export default SegmentOverrideLimit
