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
export const hasUnmatchedIdentityOverride = ({
  controlValue,
  overrideValue,
  variationOverrides,
}: {
  controlValue: FlagsmithValue
  overrideValue: FlagsmithValue
  variationOverrides: { percentage_allocation: number }[] | null | undefined
}): boolean =>
  !variationOverrides?.some(
    (variation) => variation.percentage_allocation === 100,
  ) && (overrideValue ?? null) !== (controlValue ?? null)

// Options not yet saved have no id and sort last, in input order.
export const sortMultivariateOptions = <T extends { id?: number | null }>(
  options: T[],
): T[] =>
  [...options].sort(
    (a, b) =>
      (a.id ?? Number.MAX_SAFE_INTEGER) - (b.id ?? Number.MAX_SAFE_INTEGER),
  )
