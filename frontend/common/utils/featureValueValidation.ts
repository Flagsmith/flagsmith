export const MAX_FEATURE_VALUE_LENGTH = 20_000

export function getFeatureValueLengthError(
  value: unknown,
  label = 'Flag value',
  maxLength = MAX_FEATURE_VALUE_LENGTH,
): string | undefined {
  if (typeof value !== 'string') return undefined

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
