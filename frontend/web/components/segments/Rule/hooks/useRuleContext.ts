import { OperatorValue } from 'common/types/rules.types'
import { getAllowedContextValuesForDropdown } from 'components/segments/Rule/utils'

export const useRuleContext = (operator: OperatorValue, property: string) => {
  const allowedContextValues = getAllowedContextValuesForDropdown(operator)

  const isValueFromContext = allowedContextValues.some(
    (option) => option.value === property,
  )

  return { allowedContextValues, isValueFromContext }
}
