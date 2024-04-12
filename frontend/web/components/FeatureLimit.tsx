import { FC } from 'react'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'

type FeatureLimitType = {
  project: Project | null
}

const FeatureLimit: FC<FeatureLimitType> = ({ project }) => {
  if (!project) return null
  const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
    project.total_features,
    project.max_features_allowed,
  )

  return Utils.displayLimitAlert('features', featureLimitAlert.percentage)
}

export default FeatureLimit
