import { RuleContextValues, RuleContextLabels } from 'common/types/rules.types'
import { OptionType } from 'components/base/select/SearchableSelect'

export const getAllowedContextValuesForDropdown = (
  operator: string,
): OptionType[] => {
  const baseValues: OptionType[] = [
    {
      label: RuleContextLabels.IDENTIFIER,
      value: RuleContextValues.IDENTIFIER,
    },
    {
      label: RuleContextLabels.ENVIRONMENT_NAME,
      value: RuleContextValues.ENVIRONMENT_NAME,
    },
  ]

  if (operator === 'PERCENTAGE_SPLIT') {
    return [
      {
        label: RuleContextLabels.IDENTITY_KEY,
        value: RuleContextValues.IDENTITY_KEY,
      },
      ...baseValues,
    ]
  }

  return baseValues
}

export const isContextValueValidForOperator = (
  contextValue: string | undefined,
  operator: string,
): boolean => {
  if (!contextValue) return true

  if (contextValue === RuleContextValues.IDENTITY_KEY) {
    return operator === 'PERCENTAGE_SPLIT'
  }

  return Object.values(RuleContextValues).includes(
    contextValue as RuleContextValues,
  )
}

export const shouldAutoSetIdentityKey = (
  operator: string,
  property: string | undefined,
): boolean => {
  return operator === 'PERCENTAGE_SPLIT' && !property
}
