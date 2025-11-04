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
import { RuleContextValues } from 'common/types/rules.types'
import { useRuleOperator, useRuleContext } from 'components/segments/Rule/hooks'

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
  projectId: number
}

const RuleConditionRow: React.FC<RuleConditionRowProps> = ({
  addRule,
  'data-test': dataTest,
  errors: ruleErrors,
  operators,
  projectId,
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

  const { displayValue, operator, operatorObj, valuePlaceholder } =
    useRuleOperator(rule, operators)

  const { allowedContextValues, isValueFromContext } =
    useRuleContext(operator, rule.property)

  if (rule.delete) {
    return null
  }

  const showEvaluationContextWarning = isLastRule && isValueFromContext
  const isSkippingEvaluationContextWarning =
    operator === 'PERCENTAGE_SPLIT' &&
    rule.property === RuleContextValues.IDENTITY_KEY

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
      <div
        className='d-flex flex-row align-items-center gap-1'
      >
        <div
          className='d-flex flex-1 flex-row rule align-items-center justify-content-between gap-1 col-md-10'
        >
          <div className='col-10 col-md-4'>
            <RuleConditionPropertySelect
              dataTest={`${dataTest}-property-${ruleIndex}`}
              ruleIndex={ruleIndex}
              setRuleProperty={setRuleProperty}
              propertyValue={rule.property}
              operator={rule.operator}
              allowedContextValues={allowedContextValues}
              isValueFromContext={isValueFromContext}
            />
          </div>
          {readOnly ? (
            !!find(operators, { value: operator })?.label
          ) : (
            <Select
              data-test={`${dataTest}-operator-${ruleIndex}`}
              value={operator && find(operators, { value: operator })}
              onChange={(value: { value: string }) => {
                setRuleProperty(ruleIndex, 'operator', value)
              }}
              options={operators}
              className="col-10 col-md-3"
            />
          )}
          <RuleConditionValueInput
            readOnly={readOnly}
            data-test={`${dataTest}-value-${ruleIndex}`}
            value={displayValue || ''}
            placeholder={valuePlaceholder}
            disabled={operatorObj && operatorObj.hideValue}
            projectId={projectId}
            operator={operator}
            property={rule.property}
            onChange={(value: string) => {
              setRuleProperty(ruleIndex, 'value', {
                value:
                  operatorObj && operatorObj.append
                    ? `${value}${operatorObj.append}`
                    : value,
              })
            }}
            isValid={Utils.validateRule(rule) && !ruleErrors?.value}
            className='col-10 col-md-4'
          />
        </div>
        <div className='d-flex flex-sm-column flex-md-row gap-2'>
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
        </div>
      </div>
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
              setRuleProperty(ruleIndex, 'description', { value })
            }}
          />
        </Row>
      )}

      {showEvaluationContextWarning && !isSkippingEvaluationContextWarning && (
        <Row className='mt-2'>
          <div className='d-flex align-items-center gap-1'>
            <Icon name='info-outlined' width={16} height={16} />
            <span>
              Context values are only compatible with remote evaluation
            </span>
          </div>
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
