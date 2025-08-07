import React, { useEffect, useState } from 'react'
import { components } from 'react-select/lib/components'
import Utils from 'common/utils/utils'
import { RuleContextValues } from 'common/types/rules.types'
import Constants from 'common/constants'
import { GroupLabel } from 'components/base/SearchableDropdown'
import SearchableDropdown, {
  OptionType,
} from 'components/base/SearchableDropdown'

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
  const isEditing = localCurrentValue !== propertyValue
  const showTraitOptions =
    localCurrentValue && (!isValueFromContext || isEditing)
  const traitAsGroupedOptions = showTraitOptions
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

  const showTitle = !showTraitOptions && operator !== 'PERCENTAGE_SPLIT'

  return (
    <>
      <SearchableDropdown
        dataTest={dataTest}
        value={propertyValue}
        isClearable={true}
        placeholder={'Trait / Context value'}
        options={optionsWithTrait}
        noOptionsMessage={'Start typing to select a trait'}
        onBlur={() => {
          setRuleProperty(ruleIndex, 'property', { value: localCurrentValue })
        }}
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
        displayedLabel={displayedLabel}
        components={{
          Menu: ({ ...props }: any) => {
            return (
              <components.Menu {...props}>
                <React.Fragment>
                  {showTitle && (
                    <p
                      style={{ fontStyle: 'italic', paddingTop: 6 }}
                      className='mb-0 faint text-center'
                    >
                      Pick a context or type a trait name
                    </p>
                  )}
                  {props.children}
                </React.Fragment>
              </components.Menu>
            )
          },
        }}
      />
    </>
  )
}

export default RuleConditionPropertySelect
