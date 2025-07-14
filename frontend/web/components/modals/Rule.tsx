import React, { PureComponent } from 'react'
import Constants from 'common/constants'
import cloneDeep from 'lodash/cloneDeep'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import {
  Operator,
  SegmentCondition,
  SegmentConditionsError,
  SegmentRule,
} from 'common/types/responses'
import Input from 'components/base/forms/Input'
import find from 'lodash/find'
import Button from 'components/base/forms/Button'
import RuleInputValue from './RuleInputValue'
import ErrorMessage from 'components/ErrorMessage'
import classNames from 'classnames'
import RuleTraitSelect from 'components/segments/RuleTraitSelect/RuleTraitSelect'
import { RuleContextValues } from 'common/types/rules.types'
const splitIfValue = (v: string | null | number, append: string) =>
  append && typeof v === 'string' ? v.split(append) : [v === null ? '' : v]

export default class Rule extends PureComponent<{
  index: number
  operators: Operator[]
  rule: SegmentRule
  onChange: (newValue: SegmentRule) => void
  readOnly?: boolean
  showDescription?: boolean
  'data-test'?: string
  errors: SegmentConditionsError[]
}> {
  static displayName = 'Rule'

  static propTypes = {}
  removeRule = (i: number) => {
    this.setRuleProperty(i, 'delete', { value: true })
  }

  setRuleProperty = (
    i: number,
    prop: string,
    { value }: { value: string | boolean },
  ) => {
    const rule = cloneDeep(this.props.rule)

    const { conditions: rules } = rule
    const prevOperator = Utils.findOperator(
      rules[i]?.operator,
      rules[i]?.value,
      this.props.operators,
    )
    const newOperator =
      prop !== 'operator'
        ? prevOperator
        : this.props.operators.find((v) => v.value === value)
    if (newOperator && newOperator.hideValue) {
      rules[i].value = null
    }
    if (
      (prevOperator && prevOperator.append) !==
      (newOperator && newOperator.append)
    ) {
      rules[i].value =
        splitIfValue(rules[i].value, prevOperator && prevOperator.append)[0] +
        (newOperator.append || '')
    }

    // remove append if one was added

    if (prop == 'property') {
      rules[i].property = value
    } else {
      const formattedValue =
        prop === 'value' && value !== null ? `${value}` : value

      rules[i][prop] =
        prop === 'operator' ? formattedValue?.split(':')[0] : formattedValue
    }

    if (prop === 'operator' && value === 'PERCENTAGE_SPLIT') {
      console.log(rules[i].property)
      const isPropertyContext = [
        RuleContextValues.IDENTIFIER,
        RuleContextValues.ENVIRONMENT_NAME,
      ].includes(rules[i].property)
      rules[i].property = isPropertyContext ? rules[i].property : ''
      rules[i].value = isPropertyContext ? rules[i].value : ''
    }

    if (prop === 'delete') {
      rules[i].property = { value: 'deleted' }
      rules[i].value = 'deleted'
    }

    if (!rule.conditions.filter((condition) => !condition.delete).length) {
      rule.delete = true
    }

    if (!rule.conditions.filter((condition) => !condition.delete).length) {
      rule.delete = true
    }

    this.props.onChange(rule)
  }

  addRule = () => {
    const {
      props: {
        rule: { conditions: rules },
      },
    } = this
    this.props.onChange({
      ...this.props.rule,
      conditions: rules.concat([{ ...Constants.defaultRule }]),
    })
  }

  render() {
    const {
      props: {
        rule: { conditions: rules },
      },
    } = this
    return (
      <div>
        <div className='panel-rule-wrapper overflow-visible'>
          <div className='panel-rule p-2'>
            {rules.map((rule, i) => this.renderRule(rule, i))}
          </div>
        </div>
      </div>
    )
  }

  renderRule = (rule: SegmentCondition, i: number) => {
    const {
      props: {
        operators,
        rule: { conditions: rules },
      },
    } = this
    const lastIndex = rules.reduce((acc, v, i) => {
      if (!v.delete) {
        return i
      }
      return acc
    }, 0)
    const ruleErrors = this.props.errors?.[i]

    const isLastRule = i === lastIndex
    const hasOr = i > 0
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
      <div className='rule__row reveal' key={i}>
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
          <Tooltip
            title={
              <RuleTraitSelect
                dataTest={`${this.props['data-test']}-property-${i}`}
                ruleIndex={i}
                setRuleProperty={this.setRuleProperty}
                propertyValue={rule.property}
              />
            }
            place='top'
          >
            {Constants.strings.USER_PROPERTY_DESCRIPTION}
          </Tooltip>
          {this.props.readOnly ? (
            find(operators, { value: operator })!.label
          ) : (
            <Select
              data-test={`${this.props['data-test']}-operator-${i}`}
              value={operator && find(operators, { value: operator })}
              onChange={(value: { value: string }) =>
                this.setRuleProperty(i, 'operator', value)
              }
              options={operators}
              style={{ width: '190px' }}
            />
          )}
          <RuleInputValue
            readOnly={this.props.readOnly}
            data-test={`${this.props['data-test']}-value-${i}`}
            value={value || ''}
            placeholder={valuePlaceholder}
            disabled={operatorObj && operatorObj.hideValue}
            style={{ width: '135px' }}
            onChange={(e: InputEvent) => {
              const value = Utils.getTypedValue(Utils.safeParseEventValue(e))
              this.setRuleProperty(i, 'value', {
                value:
                  operatorObj && operatorObj.append
                    ? `${value}${operatorObj.append}`
                    : value,
              })
            }}
            isValid={Utils.validateRule(rule) && !ruleErrors?.value}
          />
          {isLastRule && !this.props.readOnly ? (
            <Button
              theme='outline'
              data-test={`${this.props['data-test']}-or`}
              type='button'
              onClick={this.addRule}
            >
              Or
            </Button>
          ) : (
            <div style={{ width: 64 }} />
          )}
          <button
            data-test={`${this.props['data-test']}-remove`}
            type='button'
            id='remove-feature'
            onClick={() => this.removeRule(i)}
            className='btn btn-with-icon'
          >
            <Icon name='trash-2' width={20} fill={'#656D7B'} />
          </button>
        </Row>
        {this.props.showDescription && (
          <Row noWrap className='rule'>
            <textarea
              readOnly={this.props.readOnly}
              data-test={`${this.props['data-test']}-description-${i}`}
              className='full-width mt-2'
              value={`${rule.description || ''}`}
              placeholder='Condition description (Optional)'
              onChange={(e) => {
                const value = Utils.safeParseEventValue(e)
                this.setRuleProperty(i, 'description', value)
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
}
