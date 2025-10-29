import Utils from 'common/utils/utils'
import { Operator, SegmentCondition } from 'common/types/responses'

export const useRuleOperator = (
  rule: SegmentCondition,
  operators: Operator[],
) => {
  const operatorObj = Utils.findOperator(rule.operator, rule.value, operators)
  const operator = operatorObj?.value
  const displayValue =
    typeof rule.value === 'string'
      ? rule.value.replace(operatorObj?.append || '', '')
      : rule.value
  const valuePlaceholder = operatorObj?.hideValue
    ? 'Value (N/A)'
    : operatorObj?.valuePlaceholder || 'Value'

  return { displayValue, operator, operatorObj, valuePlaceholder }
}
