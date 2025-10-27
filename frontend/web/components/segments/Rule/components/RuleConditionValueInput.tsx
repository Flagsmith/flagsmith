import React from 'react'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'

import { getDarkMode } from 'project/darkMode'
import EnvironmentSelectDropdown from './EnvironmentSelectDropdown'
import TextAreaModal from './TextAreaModal'
import { checkWhitespaceIssues } from '../utils/whitespaceValidation'

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
  showEnvironmentDropdown?: boolean
  operator?: string
}

const RuleConditionValueInput: React.FC<RuleConditionValueInputProps> = ({
  isValid,
  onChange,
  operator,
  projectId,
  showEnvironmentDropdown,
  value,
  ...props
}) => {
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
    <div className='relative'>
      {showEnvironmentDropdown && projectId ? (
        <EnvironmentSelectDropdown
          value={value}
          onChange={(value: string) => onChange?.(value)}
          projectId={projectId}
          dataTest={props['data-test']}
        />
      ) : (
        <>
          <Input
            type='text'
            data-test={props['data-test']}
            value={value}
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
                        <TextAreaModal value={value} onChange={onChange} />,
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
        </>
      )}
    </div>
  )
}

export default RuleConditionValueInput
