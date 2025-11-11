import { OperatorValue, RuleContextValues } from 'common/types/rules.types'

export const useConditionInputType = (
  operator: OperatorValue | undefined,
  property: string | undefined,
) => {
  const showMultiEnvironmentSelect =
    operator === 'IN' && property === RuleContextValues.ENVIRONMENT_NAME

  const showSingleEnvironmentSelect =
    ['EQUAL', 'NOT_EQUAL'].includes(operator || '') &&
    property === RuleContextValues.ENVIRONMENT_NAME

  return {
    showMultiEnvironmentSelect,
    showSingleEnvironmentSelect,
  }
}
