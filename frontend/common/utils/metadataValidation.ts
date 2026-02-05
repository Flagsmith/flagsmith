import { useMemo } from 'react'
import { CustomMetadataField } from 'common/hooks/useEntityMetadataFields'

export type MetadataValidationState = {
  hasUnfilledRequired: boolean
  totalRequired: number
  totalFilledRequired: number
}

export function getGlobalMetadataValidationState(
  fields: CustomMetadataField[],
): MetadataValidationState {
  const totalRequired = fields.filter((f) => f.isRequiredFor).length
  const totalFilledRequired = fields.filter(
    (f) => f.isRequiredFor && f.field_value && f.field_value !== '',
  ).length

  return {
    hasUnfilledRequired:
      totalRequired > 0 && totalFilledRequired < totalRequired,
    totalFilledRequired,
    totalRequired,
  }
}
export function useGlobalMetadataValidation(
  fields: CustomMetadataField[],
): MetadataValidationState {
  return useMemo(() => getGlobalMetadataValidationState(fields), [fields])
}
