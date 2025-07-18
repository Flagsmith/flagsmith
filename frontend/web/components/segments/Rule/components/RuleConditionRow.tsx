import React from 'react'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import {
  Operator,
  SegmentCondition,
  SegmentConditionsError,
} from 'common/types/responses'
import find from 'lodash/find'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import RuleConditionPropertySelect from './RuleConditionPropertySelect'
import RuleConditionValueInput from './RuleConditionValueInput'

interface RuleConditionRowProps {
  rule: SegmentCondition
  ruleIndex: number
  operators: Operator[]
  readOnly?: boolean
  showDescription?: boolean
  errors?: SegmentConditionsError
  'data-test'?: string
  setRuleProperty: (
    i: number,
    prop: string,
    value: { value: string | boolean },
  ) => void
  removeRule: (i: number) => void
  addRule: () => void
  rules: SegmentCondition[]
}

const RuleConditionRow: React.FC<RuleConditionRowProps> = ({
  addRule,
  'data-test': dataTest,
  errors: ruleErrors,
  operators,
  readOnly,
  removeRule,
  rule,
  ruleIndex,
  rules,
  setRuleProperty,
  showDescription,
}) => {
  const lastIndex = rules.reduce((acc, v, i) => {
    if (!v.delete) {
      return i
    }
    return acc
  }, 0)

  const isLastRule = ruleIndex === lastIndex
  const hasOr = ruleIndex > 0
  const operatorObj = Utils.findOperator(rule.operator, rule.value, operators)
  const operator = operatorObj && operatorObj.value
  const value =
    typeof rule.value === 'string'
      ? rule.value.replace((operatorObj && operatorObj.append) || '', '')
      : rule.value

  if (rule.delete) {
    return null
  }
  const valuePlaceholder = operatorObj?.hideValue
    ? 'Value (N/A)'
    : operatorObj?.valuePlaceholder || 'Value'

  return (
    <div className='rule__row reveal' key={ruleIndex}>
      {hasOr && (
        <Row className='or-divider my-1'>
          <Row>
            <div className='or-divider__up' />
            Or
            <div className='or-divider__down' />
          </Row>
          <Flex className='or-divider__line' />
        </Row>
      )}
      <Row noWrap className='rule align-items-center justify-content-between'>
        <RuleConditionPropertySelect
          dataTest={`${dataTest}-property-${ruleIndex}`}
          ruleIndex={ruleIndex}
          setRuleProperty={setRuleProperty}
          propertyValue={rule.property}
        />
        {readOnly ? (
          !!find(operators, { value: operator })?.label
        ) : (
          <Select
            data-test={`${dataTest}-operator-${ruleIndex}`}
            value={operator && find(operators, { value: operator })}
            onChange={(value: { value: string }) =>
              setRuleProperty(ruleIndex, 'operator', value)
            }
            options={operators}
            style={{ width: '190px' }}
          />
        )}
        <RuleConditionValueInput
          readOnly={readOnly}
          data-test={`${dataTest}-value-${ruleIndex}`}
          value={value || ''}
          placeholder={valuePlaceholder}
          disabled={operatorObj && operatorObj.hideValue}
          style={{ width: '135px' }}
          onChange={(e: InputEvent) => {
            const value = Utils.getTypedValue(Utils.safeParseEventValue(e))
            setRuleProperty(ruleIndex, 'value', {
              value:
                operatorObj && operatorObj.append
                  ? `${value}${operatorObj.append}`
                  : value,
            })
          }}
          isValid={Utils.validateRule(rule) && !ruleErrors?.value}
        />
        {isLastRule && !readOnly ? (
          <Button
            theme='outline'
            data-test={`${dataTest}-or`}
            type='button'
            onClick={addRule}
          >
            Or
          </Button>
        ) : (
          <div style={{ width: 64 }} />
        )}
        <button
          data-test={`${dataTest}-remove`}
          type='button'
          id='remove-feature'
          onClick={() => removeRule(ruleIndex)}
          className='btn btn-with-icon'
        >
          <Icon name='trash-2' width={20} fill={'#656D7B'} />
        </button>
      </Row>
      {showDescription && (
        <Row noWrap className='rule'>
          <textarea
            readOnly={readOnly}
            data-test={`${dataTest}-description-${ruleIndex}`}
            className='full-width mt-2'
            value={`${rule.description || ''}`}
            placeholder='Condition description (Optional)'
            onChange={(e) => {
              const value = Utils.safeParseEventValue(e)
              setRuleProperty(ruleIndex, 'description', value)
            }}
          />
        </Row>
      )}
      {(ruleErrors?.property || ruleErrors?.value) && (
        <Row className='mt-2'>
          <ErrorMessage error={ruleErrors} />
        </Row>
      )}
    </div>
  )
}

export default RuleConditionRow
