import React, { useCallback } from 'react'
import Constants from 'common/constants'
import cloneDeep from 'lodash/cloneDeep'
import Utils from 'common/utils/utils'
import {
  Operator,
  SegmentCondition,
  SegmentConditionsError,
  SegmentRule,
} from 'common/types/responses'
import { RuleContextValues } from 'common/types/rules.types'
import RuleConditionRow from './components/RuleConditionRow'
import {
  isContextValueValidForOperator,
  shouldAutoSetIdentityKey,
  splitIfValue,
  isInvalidPercentageSplit,
} from './utils'

interface RuleProps {
  index: number
  operators: Operator[]
  rule: SegmentRule
  onChange: (newValue: SegmentRule) => void
  readOnly?: boolean
  showDescription?: boolean
  'data-test'?: string
  errors: SegmentConditionsError[]
  projectId: number
}

const Rule: React.FC<RuleProps> = ({
  'data-test': dataTest,
  errors,
  onChange,
  operators,
  projectId,
  readOnly,
  rule,
  showDescription,
}) => {
  const { conditions: rules } = rule

  const updateCondition = (
    conditionIndex: number,
    updates: Partial<SegmentCondition>,
  ) => {
    const ruleClone = cloneDeep(rule)
    Object.assign(ruleClone.conditions[conditionIndex], updates)

    if (!ruleClone.conditions.filter((condition) => !condition.delete).length) {
      ruleClone.delete = true
    }

    onChange(ruleClone)
  }

  const setConditionProperty = (conditionIndex: number, property: string) => {
    updateCondition(conditionIndex, { property })
  }

  const setConditionOperator = (
    conditionIndex: number,
    operatorValue: string,
  ) => {
    const condition = rule.conditions[conditionIndex]
    const prevOperator = Utils.findOperator(
      condition?.operator,
      condition?.value,
      operators,
    )
    const newOperator = operators.find((op) => op.value === operatorValue)

    // Split the append part of the operator as not handled by backend
    const updates: Partial<SegmentCondition> = {
      operator: operatorValue?.split(':')[0],
    }

    // Handle append changes first
    if (prevOperator?.append !== newOperator?.append) {
      const conditionValue = typeof condition?.value === 'boolean' ? String(condition.value) : condition?.value
      const cleanValue = splitIfValue(conditionValue, prevOperator?.append || '')[0]
      updates.value = cleanValue + (newOperator?.append || '')
    }

    // Clear value when changing to or from IN operator (after append handling)
    const isChangingToIn = operatorValue === 'IN'
    const isChangingFromIn = condition?.operator === 'IN'
    if (isChangingToIn || isChangingFromIn) {
      updates.value = ''
    }

    // Set null for hideValue operators (takes precedence over everything)
    if (newOperator?.hideValue) {
      updates.value = null
    } else if (prevOperator?.hideValue && !updates.hasOwnProperty('value')) {
      // When changing FROM a hideValue operator, initialize value to empty string
      updates.value = ''
    }

    if (shouldAutoSetIdentityKey(operatorValue, condition.property)) {
      updates.property = RuleContextValues.IDENTITY_KEY
    }

    if (!isContextValueValidForOperator(condition.property, operatorValue)) {
      updates.property = ''
    }

    if (operatorValue === 'PERCENTAGE_SPLIT') {
      const invalidPercentageSplit =
        condition?.value && isInvalidPercentageSplit(condition.value)
      if (invalidPercentageSplit) {
        updates.value = ''
      } else {
        updates.value = updates.value?.toString().split(':')[0]
      }
    }

    updateCondition(conditionIndex, updates)
  }

  const setConditionValue = (
    conditionIndex: number,
    value: string | boolean,
  ) => {
    const condition = rule.conditions[conditionIndex]
    if (
      condition?.operator === 'PERCENTAGE_SPLIT' &&
      isInvalidPercentageSplit(value)
    ) {
      // If the value is invalid for split, we do not update
      value = condition?.value?.toString() || ''
    }
    updateCondition(conditionIndex, { value })
  }

  const setDescriptionValue = (conditionIndex: number, description: string) => {
    updateCondition(conditionIndex, { description })
  }

  const setRuleProperty = (
    i: number,
    prop: string,
    { value }: { value: string | boolean | number },
  ) => {
    switch (prop) {
      case 'property':
        setConditionProperty(i, value as string)
        break
      case 'operator':
        setConditionOperator(i, value as string)
        break
      case 'value':
        setConditionValue(i, `${value}`)
        break
      case 'description':
        setDescriptionValue(i, value as string)
        break
      default:
        return
    }
  }

  const removeRule = (i: number) => {
    updateCondition(i, {
      delete: true,
      property: 'deleted',
      value: 'deleted',
    })
  }

  const addRule = useCallback(() => {
    const { conditions: rules } = rule
    onChange({
      ...rule,
      conditions: rules.concat([{ ...Constants.defaultRule }]),
    })
  }, [rule, onChange])

  return (
    <div className='panel-rule-wrapper overflow-visible'>
      <div className='panel-rule p-2'>
        {rules.map((ruleCondition, i) => (
          <RuleConditionRow
            key={i}
            rule={ruleCondition}
            ruleIndex={i}
            operators={operators}
            readOnly={readOnly}
            showDescription={showDescription}
            errors={errors?.[i]}
            setRuleProperty={setRuleProperty}
            removeRule={removeRule}
            addRule={addRule}
            rules={rules}
            data-test={`${dataTest}`}
            projectId={projectId}
          />
        ))}
      </div>
    </div>
  )
}

export default Rule
