import React, { useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import { RuleContextLabels, RuleContextValues } from 'common/types/rules.types'

interface RulePropertySelectProps {
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

const RulePropertySelect = ({
  dataTest,
  isTraitDisabled = false,
  propertyValue,
  ruleIndex,
  setRuleProperty,
}: RulePropertySelectProps) => {
  const [localCurrentValue, setLocalCurrentValue] = useState(propertyValue)

  useEffect(() => {
    setLocalCurrentValue(propertyValue)
  }, [propertyValue])

  const contextOptions = [
    {
      label: `${RuleContextLabels.IDENTIFIER} - Context`,
      value: RuleContextValues.IDENTIFIER,
    },
    {
      label: `${RuleContextLabels.ENVIRONMENT_NAME} - Context`,
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
      : [{ label: localCurrentValue, value: localCurrentValue }]),
    ...contextOptions,
  ]

  return (
    <>
      <Select
        data-test={`${dataTest}-property-${ruleIndex}`}
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
          // Menu: ({ ...props }: any) => {
          //     // const isOptionAvailable = props.options.filter((option: any) => option.label.includes(localCurrentValue))
          //     // console.log(isOptionAvailable)
          //     return (
          //         <components.Menu {...props}>
          //             <React.Fragment>
          //                 {!!props.selectProps?.inputValue && <div className='react-select__option'
          //                 onClick={() => {
          //                             const prop = { value: localCurrentValue, label: localCurrentValue }
          //                             // setRuleProperty(ruleIndex, 'property', prop)
          //                             // props.setValue(prop)
          //                         }}>
          //                     {/* <p
          //                         // theme='ghost'
          //                         onClick={() => {
          //                             const prop = { value: props.selectProps.inputValue, label: props.selectProps.inputValue }
          //                             setRuleProperty(index, 'property', prop)
          //                             props.setValue(prop)
          //                         }}
          //                     > */}
          //                         {/* Use "{props.selectProps.inputValue}" trait */}
          //                         {/* <div onClick={() => {
          //                             const selectedValue =  props.selectProps.inputValue
          //                             console.log('selectedValue', selectedValue)
          //                             setRuleProperty(ruleIndex, 'property', selectedValue)
          //                             // props.setValue(selectedValue)
          //                         }}>{localCurrentValue}</div> */}
          //                     {/* </p> */}
          //                 </div>
          //                 }
          //                 {props.children}
          //                 {/* {isOptionAvailable?.length > 0 && props.children} */}
          //             </React.Fragment>
          //         </components.Menu>
          //     )
          // },
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

export default RulePropertySelect
