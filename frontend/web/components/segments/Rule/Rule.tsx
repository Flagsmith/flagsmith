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

const splitIfValue = (v: string | null | number, append: string) =>
  append && typeof v === 'string' ? v.split(append) : [v === null ? '' : v]

interface RuleProps {
  index: number
  operators: Operator[]
  rule: SegmentRule
  onChange: (newValue: SegmentRule) => void
  readOnly?: boolean
  showDescription?: boolean
  'data-test'?: string
  errors: SegmentConditionsError[]
}

const Rule: React.FC<RuleProps> = ({
  'data-test': dataTest,
  errors,
  onChange,
  operators,
  readOnly,
  rule,
  showDescription,
}) => {
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

    const updates: Partial<SegmentCondition> = { operator: operatorValue }

    if (newOperator?.hideValue) {
      updates.value = null
    }

    if (prevOperator?.append !== newOperator?.append) {
      const cleanValue = splitIfValue(condition.value, prevOperator?.append)[0]
      updates.value = cleanValue + (newOperator?.append || '')
    }

    if (operatorValue === 'PERCENTAGE_SPLIT') {
      const isPropertyContext = [
        RuleContextValues.IDENTIFIER?.toString(),
        RuleContextValues.ENVIRONMENT_NAME?.toString(),
      ].includes(condition.property)

      if (!isPropertyContext) {
        updates.property = ''
        updates.value = ''
      }
    }

    updateCondition(conditionIndex, updates)
  }

  const setConditionValue = (
    conditionIndex: number,
    value: string | boolean,
  ) => {
    updateCondition(conditionIndex, { value })
  }

  const setDescriptionValue = (conditionIndex: number, description: string) => {
    updateCondition(conditionIndex, { description })
  }

  const setRuleProperty = (
    i: number,
    prop: string,
    { value }: { value: string | boolean },
  ) => {
    switch (prop) {
      case 'property':
        setConditionProperty(i, value as string)
        break
      case 'operator':
        setConditionOperator(i, value as string)
        break
      case 'value':
        setConditionValue(i, value)
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

  const { conditions: rules } = rule

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
          />
        ))}
      </div>
    </div>
  )
}

export default Rule
