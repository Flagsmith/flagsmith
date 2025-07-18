import React, { useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import { RuleContextValues } from 'common/types/rules.types'
import Constants from 'common/constants'
import Icon from 'components/Icon'

interface OptionType {
  label: string
  value: string
}

interface RuleConditionPropertySelectProps {
  ruleIndex: number
  propertyValue: string
  dataTest: string
  setRuleProperty: (
    index: number,
    property: string,
    value: { value: string | boolean },
  ) => void
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
  propertyValue,
  ruleIndex,
  setRuleProperty,
}: RuleConditionPropertySelectProps) => {
  const ALLOWED_CONTEXT_VALUES = [
    RuleContextValues.IDENTIFIER,
    RuleContextValues.ENVIRONMENT_NAME,
  ]
  const [localCurrentValue, setLocalCurrentValue] = useState(propertyValue)

  const isContextPropertyEnabled =
    Utils.getFlagsmithHasFeature('context_values')

  const contextValues: OptionType[] = JSON.parse(
    Utils.getFlagsmithValue('context_values') || '{}',
  )

  useEffect(() => {
    setLocalCurrentValue(propertyValue)
  }, [propertyValue])

  // Filter invalid context values from flagsmith and format them as options
  const contextOptions = contextValues
    ?.filter((contextValue: OptionType) =>
      ALLOWED_CONTEXT_VALUES.includes(contextValue.value as RuleContextValues),
    )
    ?.map((contextValue: OptionType) => ({
      label: contextValue?.label,
      value: contextValue?.value,
    }))

  const isValueFromContext = !!contextOptions.find(
    (option) => option.value === localCurrentValue,
  )?.value

  const displayedLabel =
    contextOptions.find((option) => option.value === propertyValue)?.label ||
    propertyValue

  const optionsWithTrait = [
    ...(isValueFromContext || !localCurrentValue
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
    ...(isContextPropertyEnabled && contextOptions?.length > 0
      ? [
          {
            label: <GroupLabel groupName='Context' />,
            options: contextValues,
          },
        ]
      : []),
  ]

  return (
    <>
      <Select
        data-test={dataTest}
        placeholder={'Trait / Context value'}
        value={{ label: displayedLabel, value: propertyValue }}
        onBlur={() => {
          setRuleProperty(ruleIndex, 'property', { value: localCurrentValue })
        }}
        isSearchable={true}
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
      />
    </>
  )
}

export default RuleConditionPropertySelect
