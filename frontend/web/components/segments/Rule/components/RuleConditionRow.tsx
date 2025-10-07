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
import { RuleContextLabels } from 'common/types/rules.types'
import { OptionType } from 'components/base/select/SearchableSelect'

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

  // TODO: Move this to the parent component in next iteration

  const ALLOWED_CONTEXT_VALUES: OptionType[] = [
    {
      enabled: operator === 'PERCENTAGE_SPLIT',
      label: RuleContextLabels.IDENTITY_KEY,
      value: RuleContextValues.IDENTITY_KEY,
    },
    {
      label: RuleContextLabels.IDENTIFIER,
      value: RuleContextValues.IDENTIFIER,
    },
    {
      label: RuleContextLabels.ENVIRONMENT_NAME,
      value: RuleContextValues.ENVIRONMENT_NAME,
    },
  ]?.filter((option) => !!option.enabled)

  const isValueFromContext = !!ALLOWED_CONTEXT_VALUES.find(
    (option) => option.value === rule.property,
  )?.value

  const showEnvironmentDropdown =
    ['EQUAL', 'NOT_EQUAL'].includes(rule.operator) &&
    rule.property === RuleContextValues.ENVIRONMENT_NAME

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
      <Row
        noWrap
        className='rule align-items-center justify-content-between gap-1'
      >
        <RuleConditionPropertySelect
          dataTest={`${dataTest}-property-${ruleIndex}`}
          ruleIndex={ruleIndex}
          setRuleProperty={setRuleProperty}
          propertyValue={rule.property}
          operator={rule.operator}
          allowedContextValues={ALLOWED_CONTEXT_VALUES || []}
          isValueFromContext={isValueFromContext}
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
          projectId={projectId}
          showEnvironmentDropdown={showEnvironmentDropdown}
          onChange={(value: string) => {
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
