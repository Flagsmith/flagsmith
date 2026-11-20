export const MAX_FEATURE_VALUE_LENGTH = 20_000

export function getFeatureValueLengthError(
  value: unknown,
  label = 'Flag value',
  maxLength = MAX_FEATURE_VALUE_LENGTH,
): string | undefined {
  if (typeof value !== 'string') return undefined
  if (value.length <= maxLength) return undefined

  const characterCount = Array.from(value).length
  if (characterCount <= maxLength) return undefined

  return `${label} is ${characterCount.toLocaleString(
    'en-GB',
  )} characters. Maximum length is ${maxLength.toLocaleString(
    'en-GB',
  )} characters.`
}

export function getFeatureValueLengthErrors(
  values: { label: string; value: unknown }[],
): string[] {
  return values.flatMap(({ label, value }) => {
    const error = getFeatureValueLengthError(value, label)
    return error ? [error] : []
  })
}

export function hasInvalidFeatureValueLength(values: unknown[]): boolean {
  return values.some((value) => !!getFeatureValueLengthError(value))
}

export function getFeatureSaveLengthErrors({
  flagValue,
  isIdentity = false,
  multivariateOptions,
  segmentOverrides,
}: {
  flagValue?: unknown
  isIdentity?: boolean
  multivariateOptions?: { key?: string | null; string_value?: unknown }[] | null
  segmentOverrides?:
    | {
        segment_name?: unknown
        toRemove?: unknown
        value?: unknown
        [key: string]: unknown
      }[]
    | null
}): string[] {
  return getFeatureValueLengthErrors([
    {
      label: isIdentity ? 'Identity override' : 'Flag value',
      value: flagValue,
    },
    ...(multivariateOptions || []).map((option, index) => ({
      label: `Variant ${option.key || index + 1} value`,
      value: option.string_value,
    })),
    ...(segmentOverrides || [])
      .filter((override) => !override.toRemove)
      .map((override, index) => ({
        label: `Segment override ${
          typeof override.segment_name === 'string' && override.segment_name
            ? override.segment_name
            : index + 1
        } value`,
        value: override.value,
      })),
  ])
}

export function formatFeatureValueLengthErrors(errors: string[]): string {
  if (errors.length <= 1) return errors[0] ?? ''
  return `${errors.length} values exceed the maximum length: ${errors.join(
    ' ',
  )}`
}
