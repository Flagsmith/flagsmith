import { FC, useEffect } from 'react'
import Utils from 'common/utils/utils'
import { useGetProjectQuery } from 'common/services/useProject'

type FeatureLimitAlertType = {
  projectId: string | number
  onChange?: (limitAlert: { percentage: number; limit: number }) => void
}

const FeatureLimitAlert: FC<FeatureLimitAlertType> = ({
  onChange,
  projectId,
}) => {
  const { data: project } = useGetProjectQuery({ id: `${projectId}` })

  const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
    project?.total_features,
    project?.max_features_allowed,
  )

  useEffect(() => {
    if (onChange && featureLimitAlert) {
      onChange(featureLimitAlert)
    }
  }, [onChange, featureLimitAlert])

  if (!featureLimitAlert.percentage) {
    return null
  }

  return (
    <>{Utils.displayLimitAlert('features', featureLimitAlert.percentage)}</>
  )
}

export default FeatureLimitAlert
