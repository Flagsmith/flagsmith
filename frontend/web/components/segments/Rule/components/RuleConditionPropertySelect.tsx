import React, { useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import { RuleContextLabels, RuleContextValues } from 'common/types/rules.types'
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
  operator: string
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
  operator,
  propertyValue,
  ruleIndex,
  setRuleProperty,
}: RuleConditionPropertySelectProps) => {
  const ALLOWED_CONTEXT_VALUES: OptionType[] = [
    {
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
  ]
  const [localCurrentValue, setLocalCurrentValue] = useState(propertyValue)

  const isContextPropertyEnabled =
    Utils.getFlagsmithHasFeature('context_values')

  useEffect(() => {
    setLocalCurrentValue(propertyValue)

    if (operator === 'PERCENTAGE_SPLIT' && !propertyValue) {
      setRuleProperty(ruleIndex, 'property', {
        value: RuleContextValues.IDENTITY_KEY,
      })
    }
  }, [propertyValue, operator, ruleIndex, setRuleProperty])

  // Filter invalid context values from flagsmith and format them as options
  const contextOptions = ALLOWED_CONTEXT_VALUES?.map(
    (contextValue: OptionType) => ({
      label: contextValue?.label,
      value: contextValue?.value,
    }),
  )

  const isValueFromContext = !!contextOptions.find(
    (option) => option.value === localCurrentValue,
  )?.value

  const displayedLabel =
    contextOptions.find((option) => option.value === propertyValue)?.label ||
    propertyValue

  const traitAsGroupedOptions =
    !isValueFromContext && localCurrentValue
      ? [
          {
            label: (
              <GroupLabel
                groupName='Traits'
                tooltipText={Constants.strings.USER_PROPERTY_DESCRIPTION}
              />
            ),
            options: [{ label: localCurrentValue, value: localCurrentValue }],
          },
        ]
      : []

  const contextAsGroupedOptions =
    isContextPropertyEnabled && contextOptions?.length > 0
      ? [
          {
            label: (
              <GroupLabel
                groupName='Context'
                tooltipText={
                  operator === 'PERCENTAGE_SPLIT'
                    ? Constants.strings.PERCENTAGE_SPLIT_DEFAULT_TO_IDENTITY_KEY
                    : undefined
                }
              />
            ),
            options: contextOptions,
          },
        ]
      : []

  const optionsWithTrait = [
    ...traitAsGroupedOptions,
    ...contextAsGroupedOptions,
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
