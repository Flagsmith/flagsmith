import Utils from 'common/utils/utils'
import { Operator, SegmentCondition } from 'common/types/responses'
import { OperatorValue } from 'common/types/rules.types'

type UseRuleOperatorResult = {
  displayValue: string | number | boolean | null
  operator: OperatorValue
  operatorObj: Operator
  valuePlaceholder: string
}

export const useRuleOperator = (
  rule: SegmentCondition,
  operators: Operator[],
): UseRuleOperatorResult => {
  const selectedOperatorObj = Utils.findOperator(
    rule.operator,
    rule.value,
    operators,
  )
  const operator = selectedOperatorObj?.value
  const displayValue =
    typeof rule.value === 'string'
      ? rule.value.replace(selectedOperatorObj?.append || '', '')
      : rule.value
  const valuePlaceholder = selectedOperatorObj?.hideValue
    ? 'Value (N/A)'
    : selectedOperatorObj?.valuePlaceholder || 'Value'

  return {
    displayValue,
    operator,
    operatorObj: selectedOperatorObj,
    valuePlaceholder,
  }
}
