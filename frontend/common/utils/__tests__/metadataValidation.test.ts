import { getGlobalMetadataValidationState } from 'common/utils/metadataValidation'
import { CustomMetadataField } from 'common/hooks/useEntityMetadataFields'

const createField = (
  partialField: Partial<CustomMetadataField> = {},
): CustomMetadataField => ({
  description: 'A test field',
  field_value: '',
  hasValue: false,
  id: 1,
  isRequiredFor: false,
  metadataModelFieldId: 1,
  name: 'Test Field',
  organisation: 1,
  type: 'str',
  ...partialField,
})

describe('getMetadataValidationState', () => {
  it('returns all zeros for empty fields array', () => {
    const result = getGlobalMetadataValidationState([])

    expect(result).toEqual({
      hasUnfilledRequired: false,
      totalFilledRequired: 0,
      totalRequired: 0,
    })
  })

  it('returns hasUnfilledRequired false when no required fields', () => {
    const fields = [
      createField({ id: 1, isRequiredFor: false }),
      createField({ id: 2, isRequiredFor: false }),
    ]

    const result = getGlobalMetadataValidationState(fields)

    expect(result).toEqual({
      hasUnfilledRequired: false,
      totalFilledRequired: 0,
      totalRequired: 0,
    })
  })

  it('returns hasUnfilledRequired false when required field is filled', () => {
    const fields = [
      createField({ field_value: 'some value', id: 1, isRequiredFor: true }),
    ]

    const result = getGlobalMetadataValidationState(fields)

    expect(result).toEqual({
      hasUnfilledRequired: false,
      totalFilledRequired: 1,
      totalRequired: 1,
    })
  })

  it('returns hasUnfilledRequired true when some required fields are unfilled', () => {
    const fields = [
      createField({ field_value: 'filled', id: 1, isRequiredFor: true }),
      createField({ field_value: '', id: 2, isRequiredFor: true }),
      createField({ field_value: '', id: 3, isRequiredFor: false }),
    ]

    const result = getGlobalMetadataValidationState(fields)

    expect(result).toEqual({
      hasUnfilledRequired: true,
      totalFilledRequired: 1,
      totalRequired: 2,
    })
  })

  it('returns hasUnfilledRequired false when all required fields are filled', () => {
    const fields = [
      createField({ field_value: 'filled', id: 1, isRequiredFor: true }),
      createField({ field_value: 'also filled', id: 2, isRequiredFor: true }),
      createField({ field_value: '', id: 3, isRequiredFor: false }),
    ]

    const result = getGlobalMetadataValidationState(fields)

    expect(result).toEqual({
      hasUnfilledRequired: false,
      totalFilledRequired: 2,
      totalRequired: 2,
    })
  })
})
