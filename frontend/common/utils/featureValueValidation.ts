export const MAX_FEATURE_VALUE_LENGTH = 20_000

function readFeatureValueLimit(container: unknown): unknown {
  if (typeof container !== 'object' || container === null) return undefined
  return Reflect.get(container, 'featureValueLimit')
}

export function getMaxFeatureValueLength(): number {
  const configured =
    readFeatureValueLimit(Reflect.get(globalThis, 'Project')) ??
    readFeatureValueLimit(Reflect.get(globalThis, 'projectOverrides'))

  if (
    typeof configured === 'number' &&
    Number.isFinite(configured) &&
    configured >= 0
  ) {
    return Math.floor(configured)
  }

  if (typeof configured === 'string' && configured.trim() !== '') {
    const parsed = Number(configured)
    if (Number.isFinite(parsed) && parsed >= 0) {
      return Math.floor(parsed)
    }
  }

  return MAX_FEATURE_VALUE_LENGTH
}

export function getFeatureValueLengthError(
  value: unknown,
  label = 'Flag value',
  maxLength = getMaxFeatureValueLength(),
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
  maxLength = getMaxFeatureValueLength(),
): string[] {
  return values.flatMap(({ label, value }) => {
    const error = getFeatureValueLengthError(value, label, maxLength)
    return error ? [error] : []
  })
}

export function hasInvalidFeatureValueLength(
  values: unknown[],
  maxLength = getMaxFeatureValueLength(),
): boolean {
  return values.some(
    (value) => !!getFeatureValueLengthError(value, 'Flag value', maxLength),
  )
}

export function getFeatureSaveLengthErrors({
  flagValue,
  isIdentity = false,
  maxLength = getMaxFeatureValueLength(),
  multivariateOptions,
  segmentOverrides,
}: {
  flagValue?: unknown
  isIdentity?: boolean
  maxLength?: number
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
  return getFeatureValueLengthErrors(
    [
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
    ],
    maxLength,
  )
}

export function formatFeatureValueLengthErrors(errors: string[]): string {
  if (errors.length <= 1) return errors[0] ?? ''
  return `${errors.length} values exceed the maximum length: ${errors.join(
    ' ',
  )}`
}
