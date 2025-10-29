import { OperatorValue, RuleContextValues } from 'common/types/rules.types'
import { getAllowedContextValuesForDropdown } from 'components/segments/Rule/utils'

export const useRuleContext = (operator: OperatorValue, property: string) => {
  const allowedContextValues = getAllowedContextValuesForDropdown(operator)

  const isValueFromContext = allowedContextValues.some(
    (option) => option.value === property,
  )
  const showEnvironmentDropdown =
    ['EQUAL', 'NOT_EQUAL'].includes(operator) &&
    property === RuleContextValues.ENVIRONMENT_NAME

  return { allowedContextValues, isValueFromContext, showEnvironmentDropdown }
}
