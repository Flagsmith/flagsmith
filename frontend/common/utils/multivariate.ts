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
  controlValue: FlagsmithValue
  overrideValue: FlagsmithValue
  variationOverrides: VariationOverrides
}): boolean =>
  !variationOverrides?.some(
    (variation) => variation.percentage_allocation === 100,
  ) && (overrideValue ?? null) !== (controlValue ?? null)

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
  overrideValue: FlagsmithValue
}): UnmatchedOverride | undefined => {
  // `null` is a valid override value, so the latch is keyed on `undefined`.
  const value =
    latchedValue === undefined && isSelected ? overrideValue : latchedValue
  return value === undefined ? undefined : { selected: isSelected, value }
}

// Options not yet saved have no id and sort last, in input order.
export const sortMultivariateOptions = <T extends { id?: number | null }>(
  options: T[],
): T[] =>
  [...options].sort(
    (a, b) =>
      (a.id ?? Number.MAX_SAFE_INTEGER) - (b.id ?? Number.MAX_SAFE_INTEGER),
  )
