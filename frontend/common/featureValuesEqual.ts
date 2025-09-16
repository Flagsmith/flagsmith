import { FeatureStateValue, FlagsmithValue } from './types/responses'

export default function featureValuesEqual(
  actualValue: FlagsmithValue,
  flagValue: FlagsmithValue,
) {
  const nullFalseyA =
    actualValue == null ||
    actualValue === '' ||
    typeof actualValue === 'undefined'
  const nullFalseyB =
    flagValue == null || flagValue === '' || typeof flagValue === 'undefined'
  return nullFalseyA && nullFalseyB ? true : actualValue === flagValue
}
