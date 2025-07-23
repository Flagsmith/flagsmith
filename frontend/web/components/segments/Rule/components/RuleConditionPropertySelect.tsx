import React, { useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import { RuleContextValues } from 'common/types/rules.types'
import Constants from 'common/constants'
import Icon from 'components/Icon'

export interface OptionType {
  enabled?: boolean
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
  allowedContextValues: OptionType[]
  isValueFromContext: boolean
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
  allowedContextValues,
  dataTest,
  isValueFromContext,
  operator,
  propertyValue,
  ruleIndex,
  setRuleProperty,
}: RuleConditionPropertySelectProps) => {
  const [localCurrentValue, setLocalCurrentValue] = useState(propertyValue)
  const isContextPropertyEnabled =
    Utils.getFlagsmithHasFeature('context_values')

  // TODO: Clean this up when enabled
  useEffect(() => {
    const isPropInvalidWithSplit =
      !propertyValue ||
      (!isContextPropertyEnabled &&
        propertyValue !== RuleContextValues.IDENTITY_KEY)
    if (operator === 'PERCENTAGE_SPLIT' && isPropInvalidWithSplit) {
      setRuleProperty(ruleIndex, 'property', {
        value: RuleContextValues.IDENTITY_KEY,
      })
    }
    setLocalCurrentValue(propertyValue)
    //eslint-disable-next-line
  }, [propertyValue, operator, ruleIndex, isContextPropertyEnabled])

  // Filter invalid context values from flagsmith and format them as options
  const contextOptions = allowedContextValues?.map(
    (contextValue: OptionType) => ({
      label: contextValue?.label,
      value: contextValue?.value,
    }),
  )

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
    contextOptions?.length > 0
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
        value={
          localCurrentValue
            ? { label: displayedLabel, value: propertyValue }
            : null
        }
        onBlur={() => {
          setRuleProperty(ruleIndex, 'property', { value: localCurrentValue })
        }}
        isSearchable={
          operator !== 'PERCENTAGE_SPLIT' || isContextPropertyEnabled
        }
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
        noOptionsMessage={() => {
          return 'Start typing to select a trait'
        }}
      />
    </>
  )
}

export default RuleConditionPropertySelect
