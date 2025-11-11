import React, { useMemo } from 'react'
import classNames from 'classnames'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'

import { getDarkMode } from 'project/darkMode'
import EnvironmentSelectDropdown from './EnvironmentSelectDropdown'
import TextAreaModal from './TextAreaModal'
import { checkWhitespaceIssues } from 'components/segments/Rule/utils'
import { MultiSelect } from 'components/base/select/multi-select'
import { safeParseArray } from 'components/segments/Rule/utils/arrayUtils'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useConditionInputType } from 'components/segments/Rule/hooks/useConditionInputType'
import { OperatorValue } from 'common/types/rules.types'

type RuleConditionValueInputProps = {
  'data-test'?: string
  value: string | number | boolean
  style?: React.CSSProperties
  placeholder?: string
  onChange?: (value: string) => void
  disabled?: boolean
  readOnly?: boolean
  isValid?: boolean
  projectId?: number
  operator?: OperatorValue
  property?: string
  className?: string
}

const RuleConditionValueInput: React.FC<RuleConditionValueInputProps> = ({
  className,
  isValid,
  onChange,
  operator,
  projectId,
  property,
  value,
  ...props
}) => {
  const { data } = useGetEnvironmentsQuery(
    { projectId: projectId?.toString() || '' },
    { skip: !projectId },
  )
  const environmentOptions = useMemo(
    () =>
      data?.results
        ? data.results.map(({ name }) => ({ label: name, value: name }))
        : [],
    [data],
  )

  const { showMultiEnvironmentSelect, showSingleEnvironmentSelect } =
    useConditionInputType(operator, property)

  if (showMultiEnvironmentSelect) {
    return (
      <div className={className}>
        <MultiSelect
          selectedValues={safeParseArray(value)}
          onSelectionChange={(selectedValues: string[]) => {
            onChange?.(selectedValues.join(','))
          }}
          placeholder='Select environments...'
          options={environmentOptions}
          className='w-100'
          hideSelectedOptions={false}
          inline
        />
      </div>
    )
  }

  if (showSingleEnvironmentSelect && projectId) {
    return (
      <div className={className}>
        <EnvironmentSelectDropdown
          value={value}
          onChange={(value: string) => onChange?.(value)}
          projectId={projectId}
          dataTest={props['data-test']}
        />
      </div>
    )
  }

  const whitespaceCheck = checkWhitespaceIssues(value, operator)
  const hasWarning = !!whitespaceCheck
  const isLongText = String(value).length >= 10

  const validate = () => {
    if (whitespaceCheck?.message) {
      return whitespaceCheck.message
    }
    if (isLongText) {
      return 'Click to edit text in a larger area'
    }
    return ''
  }

  const showIcon = hasWarning || isLongText
  const isDarkMode = getDarkMode()

  return (
    <div className={classNames('relative', className)}>
      <Input
        type='text'
        data-test={props['data-test']}
        name='rule-condition-value-input'
        aria-label='Rule condition value input'
        value={value}
        className='w-100'
        inputClassName={
          showIcon ? `pr-5 ${hasWarning ? 'border-warning' : ''}` : ''
        }
        style={{ width: '100%' }}
        onChange={(e: InputEvent) => {
          const value = Utils.safeParseEventValue(e)
          onChange?.(value)
        }}
      />
      {showIcon && (
        <div style={{ position: 'absolute', right: 5, top: 9 }}>
          <Tooltip
            title={
              <div
                className={`rule-value-icon flex ${
                  isDarkMode ? 'bg-white' : 'bg-black'
                } bg-opacity-10 rounded-2 p-1 cursor-pointer`}
                onClick={() => {
                  openModal2(
                    'Edit Value',
                    <TextAreaModal
                      value={value}
                      onChange={onChange}
                      operator={operator}
                    />,
                  )
                }}
              >
                <Icon
                  name={hasWarning ? 'warning' : 'expand'}
                  fill={
                    hasWarning
                      ? undefined
                      : `${isDarkMode ? '#fff' : '#1A2634'}`
                  }
                  width={18}
                  height={18}
                />
              </div>
            }
            place='top'
            effect='solid'
          >
            {validate()}
          </Tooltip>
        </div>
      )}
    </div>
  )
}

export default RuleConditionValueInput
