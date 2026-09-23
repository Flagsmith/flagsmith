import {
  FeatureState,
  FlagsmithValue,
  ProjectFlag,
} from 'common/types/responses'

export type FeatureChange = {
  leftEnabled: boolean
  leftValue: FlagsmithValue
  leftEnvironmentFlag: FeatureState
  rightEnabled: boolean
  rightValue: FlagsmithValue
  rightEnvironmentFlag: FeatureState
  projectFlagLeft: ProjectFlag
  projectFlagRight?: ProjectFlag
  enabledChanged: boolean
  valueChanged: boolean
  multivariateChanged: boolean
  hasDiff: boolean
}
