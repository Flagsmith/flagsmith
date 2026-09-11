import { FlagsmithValue } from 'common/types/responses'

// The label a variant displays (and is saved with) when the user never
// sets one — keep display, validation and save payloads consistent.
// Kept outside Utils so Storybook-rendered components can use it without
// pulling in Utils' store dependencies (Storybook stubs out Utils).
export const getDefaultVariantKey = (index: number): string =>
  `Variant_${index + 1}`

// An identity override made before its flag became multivariate keeps a
// free-form value. The multivariate editor only offers the environment's
// control value and each variation, so such a value has nowhere to appear:
// the control row reads as selected and the identity looks like it is on the
// environment default. Detect it so the editor can show the value, and so
// saving does not quietly replace it with the control value.
//
// Reads the current editor state, so it goes false as soon as the user picks
// the control or a variation. That drives which row is selected and what save
// writes; whether the row is listed at all is latched separately, as the value
// is only gone once saved.
// Only the allocation matters here: a variation pinned at 100% is what makes
// an override expressible as a variation rather than a free-form value.
export type VariationOverrides =
  | { percentage_allocation: number }[]
  | null
  | undefined

// An override the variation radios cannot express, and whether it is still the
// value in play.
export type UnmatchedOverride = {
  selected: boolean
  value: FlagsmithValue
}

// What a previous resolve latched: undefined until an unmatched override has
// been seen at all.
export type LatchedOverrideValue = FlagsmithValue | undefined

export const hasUnmatchedIdentityOverride = ({
  controlValue,
  overrideValue,
  variationOverrides,
}: {
  controlValue: FlagsmithValue | undefined
  overrideValue: FlagsmithValue | undefined
  variationOverrides: VariationOverrides
}): boolean =>
  // `undefined` means the feature state has not loaded, which is not the same
  // as an override of `null`. Answering from absent data would say "unmatched"
  // for any non-null control value, and the caller latches that answer for the
  // lifetime of the editor — so withhold a verdict until both sides are known.
  controlValue !== undefined &&
  overrideValue !== undefined &&
  !variationOverrides?.some(
    (variation) => variation.percentage_allocation === 100,
  ) &&
  overrideValue !== controlValue

// The editor lists an unmatched override until the modal is saved, but selects
// it only while it is still the value in play. Presence therefore latches:
// deriving it from the live predicate instead removed the row the moment a
// variation was picked, taking away both the value being replaced and the only
// way back to it. `latchedValue` carries what a previous call resolved, so
// callers hold one value rather than reimplementing the rule.
export const resolveUnmatchedOverride = ({
  isSelected,
  latchedValue,
  overrideValue,
}: {
  isSelected: boolean
  latchedValue: LatchedOverrideValue
  overrideValue: FlagsmithValue | undefined
}): UnmatchedOverride | undefined => {
  // `null` is a valid override value, so the latch is keyed on `undefined` —
  // which doubles as the not-yet-loaded state, and so never latches.
  const value =
    latchedValue === undefined && isSelected ? overrideValue : latchedValue
  return value === undefined ? undefined : { selected: isSelected, value }
}

// A variation's value is shared by every environment and only its weight is
// per environment, so a change request can carry the weight and nothing else.
export type VariationChanges = {
  values: boolean
  weights: boolean
  // New variations land at 0% allocation, so they serve nothing yet.
  added: boolean
}

type ComparableVariation = {
  id?: number | null
  key?: string | null
  type?: string | null
  string_value?: string | null
  integer_value?: number | null
  boolean_value?: boolean | null
  default_percentage_allocation?: number | null
}

export const VARIATION_VALUE_FIELDS = [
  'key',
  'type',
  'string_value',
  'integer_value',
  'boolean_value',
] as const

export const VARIATION_WEIGHT_FIELD = 'default_percentage_allocation'

const same = (a: unknown, b: unknown): boolean => (a ?? null) === (b ?? null)

export const diffVariations = ({
  edited,
  stored,
}: {
  edited: ComparableVariation[] | undefined
  stored: ComparableVariation[] | undefined
}): VariationChanges => {
  const editedList = edited ?? []
  const storedList = stored ?? []

  const isUnsaved = (variation: ComparableVariation): boolean =>
    variation.id === null || variation.id === undefined
  const added = editedList.some(isUnsaved)
  const removed = storedList.some(
    (storedVariation) =>
      !editedList.some((variation) => variation.id === storedVariation.id),
  )

  let values = removed
  let weights = false

  for (const variation of editedList) {
    if (isUnsaved(variation)) {
      continue
    }
    const before = storedList.find((candidate) => candidate.id === variation.id)
    if (!before) {
      continue
    }
    if (
      VARIATION_VALUE_FIELDS.some(
        (field) => !same(variation[field], before[field]),
      )
    ) {
      values = true
    }
    if (
      !same(
        variation.default_percentage_allocation,
        before.default_percentage_allocation,
      )
    ) {
      weights = true
    }
  }

  return { added, values, weights }
}

// Without this, an unchanged feature state is filed and approvers get an
// empty request.
export const hasApprovableChanges = ({
  editedEnabled,
  editedValue,
  segmentOverridesChanged,
  storedEnabled,
  storedValue,
  weightsChanged,
}: {
  editedEnabled: boolean | undefined
  editedValue: FlagsmithValue | undefined
  segmentOverridesChanged: boolean
  storedEnabled: boolean | undefined
  storedValue: FlagsmithValue | undefined
  weightsChanged: boolean
}): boolean =>
  weightsChanged ||
  segmentOverridesChanged ||
  !same(editedEnabled, storedEnabled) ||
  !same(editedValue, storedValue)

// Options not yet saved have no id and sort last, in input order.
export const sortMultivariateOptions = <T extends { id?: number | null }>(
  options: T[],
): T[] =>
  [...options].sort(
    (a, b) =>
      (a.id ?? Number.MAX_SAFE_INTEGER) - (b.id ?? Number.MAX_SAFE_INTEGER),
  )
