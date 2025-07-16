import React, { useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import { RuleContextLabels, RuleContextValues } from 'common/types/rules.types'
import Constants from 'common/constants'
import Icon from 'components/Icon'

interface RuleConditionPropertySelectProps {
  ruleIndex: number
  propertyValue: string
  dataTest: string
  setRuleProperty: (
    index: number,
    property: string,
    value: { value: string | boolean },
  ) => void
  isTraitDisabled?: boolean
}

const GroupLabel = ({
  groupName,
  tooltipText,
}: {
  groupName: string
  tooltipText?: string
}) => {
  return (
    <div className='d-flex align-items-center gap-1'>
      <div>{groupName}</div>
      {tooltipText && (
        <Tooltip
          title={
            <h5 className='mb-1 cursor-pointer'>
              <Icon name='info-outlined' height={16} width={16} />
            </h5>
          }
          place='right'
        >
          {tooltipText}
        </Tooltip>
      )}
    </div>
  )
}

const RuleConditionPropertySelect = ({
  dataTest,
  isTraitDisabled = false,
  propertyValue,
  ruleIndex,
  setRuleProperty,
}: RuleConditionPropertySelectProps) => {
  const [localCurrentValue, setLocalCurrentValue] = useState(propertyValue)

  useEffect(() => {
    setLocalCurrentValue(propertyValue)
  }, [propertyValue])

  const contextOptions = [
    {
      label: `${RuleContextLabels.IDENTIFIER}`,
      value: RuleContextValues.IDENTIFIER,
    },
    {
      label: `${RuleContextLabels.ENVIRONMENT_NAME}`,
      value: RuleContextValues.ENVIRONMENT_NAME,
    },
  ]

  const isValueFromContext = !!contextOptions.find(
    (option) => option.value === localCurrentValue,
  )?.value
  const label =
    contextOptions.find((option) => option.value === propertyValue)?.label ||
    propertyValue

  const optionsWithTrait = [
    ...(isValueFromContext || !localCurrentValue || isTraitDisabled
      ? []
      : [
          {
            label: (
              <GroupLabel
                groupName='Traits'
                tooltipText={Constants.strings.USER_PROPERTY_DESCRIPTION}
              />
            ),
            options: [{ label: localCurrentValue, value: localCurrentValue }],
          },
        ]),
    {
      label: (
        <GroupLabel
          groupName='Context'
          tooltipText={
            isTraitDisabled
              ? Constants.strings.TRAITS_DISABLED_FOR_OPERATOR
              : undefined
          }
        />
      ),
      options: contextOptions,
    },
  ]
  console.log('dataTest', dataTest)
  return (
    <>
      <Select
        inputId={`${dataTest}`}
        data-test={dataTest}
        placeholder={'Trait / Context value'}
        value={{ label: label, value: propertyValue }}
        onBlur={() => {
          setRuleProperty(ruleIndex, 'property', { value: localCurrentValue })
        }}
        isSearchable={!isTraitDisabled}
        onInputChange={(e: string, metadata: any) => {
          if (metadata.action !== 'input-change') {
            return
          }
          setLocalCurrentValue(e)
        }}
        onChange={(e: { value: string; label: string }) => {
          setRuleProperty(ruleIndex, 'property', {
            value: Utils.safeParseEventValue(e?.value),
          })
        }}
        options={[...optionsWithTrait]}
        style={{ width: '200px' }}
        noOptionsMessage={() => ''}
        components={{
          Option: ({ children, data, innerProps, innerRef }: any) => (
            <div
              ref={innerRef}
              {...innerProps}
              className='react-select__option'
            >
              {!!data.feature && (
                <div className='unread ml-2 px-2'>Feature-Specific</div>
              )}
              {children}
            </div>
          ),
        }}
      />
    </>
  )
}

export default RuleConditionPropertySelect
