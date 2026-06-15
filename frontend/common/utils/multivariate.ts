// The label a variant displays (and is saved with) when the user never
// sets one — keep display, validation and save payloads consistent.
// Kept outside Utils so Storybook-rendered components can use it without
// pulling in Utils' store dependencies (Storybook stubs out Utils).
export const getDefaultVariantKey = (index: number): string =>
  `Variant_${index + 1}`

// Options not yet saved have no id and sort last, in input order.
export const sortMultivariateOptions = <T extends { id?: number | null }>(
  options: T[],
): T[] =>
  [...options].sort(
    (a, b) =>
      (a.id ?? Number.MAX_SAFE_INTEGER) - (b.id ?? Number.MAX_SAFE_INTEGER),
  )
