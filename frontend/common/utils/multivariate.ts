// The label a variant displays (and is saved with) when the user never
// sets one — keep display, validation and save payloads consistent.
// Kept outside Utils so Storybook-rendered components can use it without
// pulling in Utils' store dependencies (Storybook stubs out Utils).
export const getDefaultVariantKey = (index: number): string =>
  `Variant_${index + 1}`
